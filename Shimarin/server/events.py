import asyncio
import inspect
import uuid
from datetime import datetime
from typing import Callable, Any


class Event:
    def __init__(self, event_type: str, payload: str = None, callback: Callable |  None = None):
        self.event_type = event_type
        self.payload = payload
        self.callback = callback
        self.identifier = str(uuid.uuid1())
        self.answered = True if callback is None else False
        self.__answer = ""
        self.__creation_date = datetime.now()
        self.done = False

    @staticmethod
    def new(event_type: str, payload: str = None, callback: Callable |  None = None) -> 'Event':
        return Event(event_type, payload, callback)
    
    @property
    def age(self):
        return datetime.now() - self.__creation_date
    
    @property
    def answer(self):
        self.done = True
        return self.__answer
    
    async def get_answer(self):
        while self.answered is False:
            await asyncio.sleep(0)
        return self.answer

    def json(self) -> dict:
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "identifier": self.identifier
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


class EventEmitter:
    def __init__(self):
        self.events: list[Event] = []

    async def fetch_event(self, last: bool = True) -> Event:
        try:
            return self.events.pop(0 if not last else -1)
        except IndexError:
            return Event(None, None, None)
        
    async def send(self, event: Event) -> None:
        self.events.append(event)


class CallbacksHandlers:
    def __init__(self):
        self.events: list[Event] = []

    async def clear_done(self):
        for event in self.events.copy():
            if event.done:
                self.events.remove(event)

    async def register(self, event: Event):
        await self.clear_done()
        self.events.append(event)

    async def handle(self, unique_identifier: str, payload: Any):
        await self.clear_done()
        for event in self.events:
            if event.identifier == unique_identifier:
                return await event.trigger(payload)
