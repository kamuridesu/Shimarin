from abc import ABC, abstractmethod
from typing import Literal

from Shimarin.server.event import Event


class PersistenceMiddleware(ABC):

    @abstractmethod
    def register(self, ev: Event) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, last=False) -> Event:
        raise NotImplementedError

    @abstractmethod
    def get(self, identifier: str) -> Event:
        raise NotImplementedError

    @abstractmethod
    def update_event_status(
        self,
        ev: Event,
        status: Literal["delivered", "done", "failed", "waiting"],
    ):
        raise NotImplementedError

    @abstractmethod
    def prune_finished(self, remove_failed=False) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove(self, event_id: str) -> None:
        raise NotImplementedError
