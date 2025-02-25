import json
import os
from dataclasses import dataclass
from typing import Callable

from flask import Blueprint, Flask, request

from Shimarin.server import events

CONTEXT_PATH = os.getenv("CONTEXT_PATH", "")


@dataclass
class LoginResponse:
    ok: bool
    status: int
    message: str

    def as_response(self):
        return {"ok": self.ok, "message": self.message}, self.status


INVALID_CREDENTIAL_RESPONSE = LoginResponse(False, 401, "Invalid credentials!")
DISABLED_RESPONSE = LoginResponse(True, 200, "Authentication disabled")
VALID_CREDENTIAL_RESPONSE = LoginResponse(True, 200, "Logged in!")


def login():
    env_user = os.getenv("SHIMARIN_USERNAME", "")
    env_pw = os.getenv("SHIMARIN_PASSWORD", "")

    if env_user == "" and env_pw == "":
        return DISABLED_RESPONSE

    username = request.headers.get("username")
    password = request.headers.get("password")

    if username == env_user and env_pw == password:
        return VALID_CREDENTIAL_RESPONSE
    else:
        return INVALID_CREDENTIAL_RESPONSE


class ShimaApp(Blueprint):
    def __init__(
        self,
        emitter: events.EventEmitter,
        login_callback: Callable[[], LoginResponse] = login,
        use_stream_response=False
    ):
        super().__init__("ShimaServer", __name__)
        self.login_callback = login_callback
        self.emitter = emitter
        self.use_stream_response = use_stream_response
        self.add_url_rule(
            CONTEXT_PATH + "/events", None, self.fetch, methods=["GET"]
        )
        self.add_url_rule(
            CONTEXT_PATH + "/callback", None, self.callback, methods=["POST"]
        )

    async def fetch(self):
        r = self.login_callback()
        if r.ok is False:
            return r.as_response()
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

    async def callback(self):
        r = self.login_callback()
        if r.ok is False:
            return r.as_response()
        identifier = request.headers.get("x-identifier")
        metadata = json.loads(request.headers.get("X-Metadata", ""))
        payload = request.stream if self.use_stream_response else request.get_data(cache=False)
        if identifier and payload:
            await self.emitter.handle(identifier, payload, metadata)
        return {"ok": True}


if __name__ == "__main__":
    app = Flask("server")
    fa = ShimaApp(events.EventEmitter())
    app.register_blueprint(fa)
    app.run(debug=True, host="0.0.0.0", port=2222)
