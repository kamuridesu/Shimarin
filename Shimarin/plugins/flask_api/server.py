import os

from Shimarin.server import events
from flask import Flask, request


emitter = events.EventEmitter()
app = Flask("server")


def login():
    if ((USERNAME := os.getenv("SHIMARIN_USERNAME") and (PASSWORD := os.getenv("SHIMARIN_PASSWORD")))):
        if (username := request.headers.get("username")) and (
            password := request.headers.get("password")
        ):
            if username != USERNAME or password != PASSWORD:
                return {"ok": False, "message": "Invalid credentials!"}, 401
        else:
            return {"ok": False, "message": "Invalid credentials!"}, 401
    return {"ok": True, "message": "Authentication disabled"}


@app.route("/events", methods=["GET"])
async def events_route():
    r = login()
    if (r['ok'] is False):
        return r
    fetch = request.args.get("fetch")
    events_to_send = 1
    if fetch:
        events_to_send = int(fetch)
    events = []
    for _ in range(events_to_send):
        last_ev = await emitter.fetch_event()
        if last_ev.event_type:
            events.append(last_ev.json())
    return events


@app.route("/callback")
async def reply_route():
    r = login()
    if (r['ok'] is False):
        return r
    data = request.get_json(silent=True)
    if data:
        identifier = data["identifier"]
        payload = data["payload"]
        print("triggering")
        await emitter.handle(identifier, payload)
    return {"ok": True}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=2222)
