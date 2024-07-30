from abc import ABC, abstractmethod
from typing import Literal

from ...server.event import Event


class PersistenceMiddleware(ABC):

    @abstractmethod
    def register(self, ev: Event) -> None:
        return NotImplemented
    
    @abstractmethod
    def fetch(self, last = False) -> Event:
        return NotImplemented
    
    @abstractmethod
    def get(self, identifier: str) -> Event:
        return NotImplemented
    
    @abstractmethod
    def update_event_status(self, identifier: str, status: Literal['delivered', 'done', 'failed', 'waiting'], ev: Event):
        return NotImplemented
    
    @abstractmethod
    def prune_finished(self, remove_failed = False) -> None:
        return NotImplemented

    @abstractmethod
    def remove(self, event_id: str) -> None:
        return NotImplemented
