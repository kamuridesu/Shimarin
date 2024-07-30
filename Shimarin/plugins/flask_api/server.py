import os

from ...server import events
from flask import Flask, request, Blueprint


CONTEXT_PATH = os.getenv("CONTEXT_PATH", "")


def login():
    if ((USERNAME := os.getenv("SHIMARIN_USERNAME") and (PASSWORD := os.getenv("SHIMARIN_PASSWORD")))):
        if (username := request.headers.get("username")) and (
            password := request.headers.get("password")
        ):
            if username != USERNAME or password != PASSWORD:
                return {"ok": False, "message": "Invalid credentials!"}, 401
        else:
            return {"ok": False, "message": "Invalid credentials!"}, 401
    return {"ok": True, "message": "Authentication disabled"}, 200


class FlaskApp:
    blueprint = Blueprint("ShimaServer", __name__)

    def __init__(self, emitter: events.EventEmitter):
        self.emitter = emitter
        self.blueprint.add_url_rule(CONTEXT_PATH + "/events", None, self.events_route, methods=["GET"])
        self.blueprint.add_url_rule(CONTEXT_PATH + "/callback", None, self.reply_route, methods=["GET"])

    async def events_route(self):
        r = login()
        if (r[0]['ok'] is False):
            return r
        fetch = request.args.get("fetch")
        events_to_send = 1
        if fetch:
            events_to_send = int(fetch)
        events = []
        for _ in range(events_to_send):
            last_ev = await self.emitter.fetch_event()
            if last_ev:
                events.append(last_ev.json())
        return events
    
    async def reply_route(self):
        r = login()
        if (r[0]['ok'] is False):
            return r
        data = request.get_json(silent=True)
        if data:
            identifier = data["identifier"]
            payload = data["payload"]
            await self.emitter.handle(identifier, payload)
        return {"ok": True}


if __name__ == "__main__":
    app = Flask("server")
    fa = FlaskApp(events.EventEmitter())
    app.register_blueprint(fa.blueprint)
    app.run(debug=True, host="0.0.0.0", port=2222)
