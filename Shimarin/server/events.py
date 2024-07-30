import asyncio
from typing import Any
from datetime import datetime

from .exceptions import EventAnswerTimeoutError

from .event import Event
from ..plugins.middleware.persistence import PersistenceMiddleware


class EventEmitter:
    def __init__(self, max_age_seconds: float = 0, persistence_middleware: PersistenceMiddleware | None = None):
        self.events: list[Event] = []
        self.max_age_seconds = max_age_seconds
        self.persistence_middleware = persistence_middleware

    async def get_answer(self, event_id: str, default: Any | None = None, timeout = 60) -> Event:
        ev = default
        start = datetime.now()
        while True:
            await asyncio.sleep(0)
            if (datetime.now() - start).total_seconds() >= timeout:
                raise EventAnswerTimeoutError
            if (self.persistence_middleware is not None):
                event = self.persistence_middleware.get(event_id)
                if event:
                    ev = event
            else:
                for event in self.events:
                    if event.identifier == event_id:
                        ev = event
            if ev != None and ev.answered:
                return ev.answer
            if ev is None:
                return

    async def clean_old_items(self):
        for event in [x for x in self.events if x.status in ['done', 'failed']]:
            if ((event.age >= self.max_age_seconds) if (self.max_age_seconds > 0) else False):
                self.events.remove(event)
        if self.persistence_middleware:
            self.persistence_middleware.prune_finished()

    async def fetch_event(self, last: bool = True) -> Event:
        await self.clean_old_items()
        item = None
        try:
            if self.persistence_middleware is not None:
                item = self.persistence_middleware.fetch(last)
            else:
                item: Event = [x for x in self.events if x.status == 'waiting'].pop(0 if not last else -1)
            if item is not None:
                item.status = 'delivered'
            return item
        except IndexError:
            return item

    async def send(self, event: Event) -> None:
        await self.clean_old_items()
        if (self.persistence_middleware is not None):
            return self.persistence_middleware.register(event)
        self.events.append(event)

    async def handle(self, unique_identifier: str, payload: Any):
        await self.clean_old_items()
        if (self.persistence_middleware is not None):
            ev = self.persistence_middleware.get(unique_identifier)
            if ev:
                response = await ev.trigger(payload)
                self.persistence_middleware.update_event_status(ev.identifier, 'done', ev)
                return response
        else:
            for event in self.events:
                if event.identifier == unique_identifier:
                    return await event.trigger(payload)
