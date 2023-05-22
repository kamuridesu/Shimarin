import aiohttp
import asyncio
import json
import logging

from typing import Callable, Any

from .config import config
from .networking import send_get_request, Response


logger = logging.getLogger("Shimarin")


class Event:
    def __init__(
        self,
        event_type: str,
        identifier: str,
        payload: str | None,
        session: aiohttp.ClientSession,
        server_endpoint: str = config.SERVER_ENDPOINT,
        custom_headers: dict = {},
    ) -> None:
        self.event_type = event_type
        self.payload = payload
        self.identifier = identifier
        self.__session = session
        self.server_endpoint = server_endpoint
        self.custom_headers = custom_headers

    @staticmethod
    def new(
        event_data: dict[str, str],
        session: aiohttp.ClientSession | None,
        server_endpoint: str = config.SERVER_ENDPOINT,
        custom_headers: dict = {},
    ) -> "Event":
        return Event(
            event_data["event_type"],
            event_data["identifier"],
            event_data["payload"],
            session,
            server_endpoint,
            custom_headers,
        )

    async def reply(self, payload: Any):
        data = {"identifier": str(self.identifier), "payload": json.dumps(payload)}
        await send_get_request(
            self.__session,
            f"{self.server_endpoint}/callback",
            json=data,
            headers=self.custom_headers,
        )

    def __str__(self) -> str:
        return f"Event: {self.event_type}, Identifier: {self.identifier}, Payload: {self.payload}"

    def __repr__(self) -> str:
        return self.__str__()


class EventHandler:
    def __init__(self, event_type: str, callback: Callable[[Any, Any], Any]) -> None:
        self.event_type = event_type
        self.callback = callback

    async def trigger(self, *args, **kwargs) -> None:
        await self.callback(*args, **kwargs)

    def __str__(self) -> str:
        return f"Event: {self.event_type}, Callback: {self.callback}"

    def __repr__(self) -> str:
        return self.__str__()


class EventsHandlers:
    def __init__(self):
        self.handlers: list[EventHandler] = []

    def register(self, handler: EventHandler) -> None:
        self.handlers.append(handler)

    def new(self, event_name: str):
        def wrapper(func: Callable):
            event_handler = EventHandler(event_name, func)
            self.register(event_handler)
            return func

        return wrapper

    async def handle(self, event: Event) -> None:
        for handle in self.handlers:
            if handle.event_type == event.event_type:
                asyncio.gather(handle.trigger(event))

    def __str__(self) -> str:
        return f"Handlers: {self.handlers}"

    def __repr__(self) -> str:
        return self.__str__()


class EventPolling:
    def __init__(self, events_handlers: EventsHandlers) -> None:
        self.session = aiohttp.ClientSession()
        self.events_handlers = events_handlers
        self.is_polling = False
        self.running_tasks: set[asyncio.Task] = set()

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, tb)

    async def start(
        self,
        polling_interval: int = 1,
        fetch: int = 10,
        custom_headers: dict = {},
        server_endpoint: str = config.SERVER_ENDPOINT,
        retries: int = 5,
    ):
        self.is_polling = True
        while self.is_polling:
            for _ in range(retries):
                try:
                    events: Response = await send_get_request(
                        self.session,
                        f"{server_endpoint}/events?fetch={fetch}",
                        headers=custom_headers,
                    )

                    if events.status == 200:
                        event_json = await events.json()
                        for event in event_json:
                            if event_json:
                                event = Event.new(
                                    event, self.session, server_endpoint, custom_headers
                                )
                                await self.__task_manager(event)
                        break
                    raise aiohttp.ServerConnectionError
                except (
                    aiohttp.ClientError,
                    aiohttp.ServerTimeoutError,
                    aiohttp.ServerDisconnectedError,
                    aiohttp.ServerConnectionError,
                    aiohttp.ClientConnectionError,
                ):
                    logger.warning(
                        f"Error connecting to {server_endpoint}! Retrying..."
                    )
                    await asyncio.sleep(1)
            await asyncio.sleep(polling_interval)

    async def __task_manager(self, event: Event):
        task = asyncio.create_task(self.events_handlers.handle(event))
        self.running_tasks.add(task)
        task.add_done_callback(lambda t: self.running_tasks.remove(t))

    async def stop(self):
        if self.is_polling:
            self.is_polling = False
            for task in self.running_tasks:
                task.cancel()
            for task in self.running_tasks.copy():
                self.running_tasks.remove(task)
