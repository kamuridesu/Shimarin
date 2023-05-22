import asyncio
import inspect
import uuid
from datetime import datetime
from typing import Callable, Any

from .exceptions import EventAnswerTimeoutError


class Event:
    def __init__(
        self, event_type: str, payload: str = None, callback: Callable | None = None
    ):
        self.event_type = event_type
        self.payload = payload
        self.callback = callback
        self.identifier = str(uuid.uuid1())
        self.answered = True if callback is None else False
        self.__answer = ""
        self.__creation_date = datetime.now()
        self.done = False
        self.delete = False  # this config will be used later when callbacks are merged into emitter

    @staticmethod
    def new(
        event_type: str, payload: str = None, callback: Callable | None = None
    ) -> "Event":
        return Event(event_type, payload, callback)

    @property
    def age(self):
        return (datetime.now() - self.__creation_date).total_seconds()

    @property
    def answer(self):
        self.done = True
        return self.__answer

    async def get_answer(self, timeout: float = 0):
        start = datetime.now()
        while self.answered is False:
            await asyncio.sleep(0)
            if (datetime.now() - start).total_seconds() >= timeout:
                raise EventAnswerTimeoutError
        return self.answer

    def json(self) -> dict:
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "identifier": self.identifier,
        }

    def __repr__(self):
        return self.json().__str__()

    async def trigger(self, payload: Any):
        self.answered = True
        if inspect.iscoroutinefunction(self.callback):
            self.__answer = await self.callback(payload)
        else:
            self.__answer = self.callback(payload)
        return self.__answer


class CallbacksHandlers:
    def __init__(self):
        self.events: list[Event] = []

    async def register(self, event: Event):
        self.events.append(event)

    async def handle(self, unique_identifier: str, payload: Any):
        for event in self.events:
            if event.identifier == unique_identifier:
                return await event.trigger(payload)


class EventEmitter:
    def __init__(self, max_age_seconds: float = 0):
        self.events: list[Event] = []
        self.handlers = CallbacksHandlers()
        self.max_age_seconds = max_age_seconds

    async def clean_old_items(self):
        for event in self.events.copy():
            if event.done or ((event.age >= self.max_age_seconds) if (self.max_age_seconds > 0) else False):
                self.events.remove(event)
        for event in self.handlers.events.copy():
            if event.done or ((event.age >= self.max_age_seconds) if (self.max_age_seconds > 0) else False):
                self.handlers.events.remove(event)

    async def fetch_event(self, last: bool = True) -> Event:
        await self.clean_old_items()
        try:
            item = self.events.pop(0 if not last else -1)
            await self.handlers.register(item)
            return item
        except IndexError:
            return Event(None, None, None)

    async def send(self, event: Event) -> None:
        await self.clean_old_items()
        self.events.append(event)

    async def handle(self, unique_identifier: str, payload: Any):
        await self.clean_old_items()
        return await self.handlers.handle(unique_identifier, payload)
