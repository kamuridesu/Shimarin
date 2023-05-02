import asyncio
import json
from Shimarin.server import events
from flask import Flask, request


emitter = events.EventEmitter()
callbacks = events.CallbacksHandlers()


app = Flask("server")


@app.route("/events", methods=["GET"])
async def events_route():
    fetch = request.args.get('fetch')
    events_to_send = 1
    if fetch:
        events_to_send = int(fetch)
    events = []
    for _ in range(events_to_send):
        last_ev = await emitter.fetch_event()
        if last_ev.event_type:
            await callbacks.register(last_ev)
            events.append(last_ev.json())
    return events


@app.route("/callback")
async def reply_route():
    data = request.get_json(silent=True)
    if data:
        identifier = data['identifier']
        payload = data['payload']
        await callbacks.handle(identifier, payload)
    return {"ok": True}


async def handle_test(params: dict = {}):
    event = events.Event.new("update", json.dumps(params), json.loads)
    await emitter.send(event)
    answer = await event.get_answer()
    return answer


@app.route("/test", methods=["GET"])
async def test_route():
    args = request.get_json(force=True, silent=True)
    if args is None:
        args = {}
    return (await handle_test(args))
 


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=2222)
