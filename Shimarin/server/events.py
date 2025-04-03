import asyncio
from datetime import datetime
from typing import Any, cast

from Shimarin.plugins.middleware.persistence import PersistenceMiddleware
from Shimarin.server.event import CallbackArguments, CallbackMetadata, Event
from Shimarin.server.exceptions import EventAnswerTimeoutError


class EventEmitter:
    def __init__(
        self,
        max_age_seconds: float = 0,
        persistence_middleware: PersistenceMiddleware | None = None,
    ):
        self.events: list[Event[Any]] = []
        self.max_age_seconds = max_age_seconds
        self.persistence_middleware = persistence_middleware
        self.cleanup_task: asyncio.Task | None = asyncio.get_event_loop().create_task(
            self.clean_old_items()
        )

    async def get_answer(self, event_id: str, timeout=60):
        start = datetime.now()
        ev: Event[Any] | None = None
        while True:
            await asyncio.sleep(0.1)
            if (datetime.now() - start).total_seconds() >= timeout:
                if ev:
                    ev.status = "failed"
                    if self.persistence_middleware:
                        self.persistence_middleware.update_event_status(ev, "failed")
                raise EventAnswerTimeoutError
            if self.persistence_middleware is not None:
                event = self.persistence_middleware.get(event_id)
                if event:
                    ev = cast(Event[Any], event)
            else:
                for event in self.events:
                    if event.identifier == event_id:
                        ev = cast(Event[Any], event)
            if ev != None and ev.answered:
                return cast(Any, ev.answer)

    async def clean_old_items(self):
        while True:
            for event in [x for x in self.events if x.status in ["done", "failed"]]:
                is_failed_event = event.status == "failed" or (
                    (event.age >= self.max_age_seconds)
                    if self.max_age_seconds
                    else False
                )
                if is_failed_event:
                    self.events.remove(event)
            if self.persistence_middleware:
                self.persistence_middleware.prune_finished()
            await asyncio.sleep(1)

    async def fetch_event(self, last: bool = True) -> Event | None:
        item: Event | None = None
        try:
            if self.persistence_middleware is not None:
                item = self.persistence_middleware.fetch(last)
            else:
                item = [x for x in self.events if x.status == "waiting"].pop(
                    0 if not last else -1
                )
            if item is not None:
                item.status = "delivered"
            return item
        except IndexError:
            return item

    async def send(self, event: Event) -> None:
        if self.persistence_middleware is not None:
            return self.persistence_middleware.register(event)
        self.events.append(event)

    async def handle(
        self,
        unique_identifier: str,
        payload: CallbackArguments,
        metadata: CallbackMetadata = None,
    ):
        if self.persistence_middleware is not None:
            ev = self.persistence_middleware.get(unique_identifier)
            if ev:
                response = await ev.trigger(payload, metadata)
                self.persistence_middleware.update_event_status(ev, "done")
                return response
        else:
            for event in self.events:
                if event.identifier == unique_identifier:
                    return await event.trigger(payload, metadata)
