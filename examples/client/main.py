import asyncio
from Shimarin.client import events


handlers = events.EventsHandlers()


@handlers.new("update")
async def update(event: events.Event):
    return await event.reply("Yes")


async def main():
    async with events.EventPolling(handlers) as poller:
        await poller.start(0.1, server_endpoint="http://localhost:2222")


if __name__ == "__main__":
    asyncio.run(main())
