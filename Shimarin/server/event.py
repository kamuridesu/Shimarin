import asyncio
import inspect
import uuid
from datetime import datetime
from typing import Callable, Any, Literal

from .exceptions import CallbackIsLambdaError, UnknownStatusError


class Event:
    def __init__(
        self, event_type: str, payload: str = None, callback: Callable | None = None
    ):
        if inspect.isfunction(callback) and callback.__name__ == "<lambda>":
            raise CallbackIsLambdaError
        self.event_type = event_type
        self.payload = payload
        self.callback = callback
        self.identifier = str(uuid.uuid1())
        self.answered = True if callback is None else False
        self.__answer = ""
        self.__creation_date = datetime.now()
        self.__status: Literal['delivered', 'done', 'failed', 'waiting'] = "waiting"

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
        return self.__answer
    
    @answer.setter
    def answer(self, data):
        self.__answer = data
        self.answered = True
        self.status = 'done'
    
    @property 
    def status(self):
        return self.__status
    
    @status.setter
    def status(self, status_text: Literal['delivered', 'done', 'failed', 'waiting']):
        if status_text not in ['delivered', 'done', 'failed', 'waiting']:
            raise UnknownStatusError
        self.__status = status_text

    def json(self) -> dict:
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "identifier": self.identifier,
            "status": self.__status
        }

    def __repr__(self):
        return self.json().__str__()

    async def trigger(self, payload: Any):
        self.answered = True
        if inspect.iscoroutinefunction(self.callback):
            self.answer = await self.callback(payload)
        else:
            self.answer = self.callback(payload)
        return self.answer
