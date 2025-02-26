import json
from typing import Literal

from flask import Flask, request

from Shimarin.plugins.flask_api import ShimaApp
from Shimarin.plugins.middleware.sqlite_middleware import SQLitePersistenceMiddleware
from Shimarin.server.events import (
    CallbackArguments,
    CallbackMetadata,
    Event,
    EventEmitter,
)
from Shimarin.server.exceptions import EventAnswerTimeoutError

app = Flask("server")
emitter = EventEmitter(persistence_middleware=SQLitePersistenceMiddleware("test.db"))


def callback(params: CallbackArguments, metadata: CallbackMetadata) -> str | None:
    print(metadata)
    if metadata:
        print("Name: " + metadata.get("name", ""))
    if isinstance(params, bytes):
        return json.dumps(params.decode())


async def handle_test(params: dict = {}) -> str | Literal["fail"]:
    event = Event("update", json.dumps(params), callback)
    await emitter.send(event)
    print("waiting for answer")
    try:
        return await emitter.get_answer(
            event.identifier, timeout=60
        )  # 1 minute timeout
    except EventAnswerTimeoutError:
        return "fail"


@app.route("/test", methods=["GET"])
async def test_route():
    args = request.get_json(force=True, silent=True)
    if args is None:
        args = {}
    return await handle_test(args), 200


if __name__ == "__main__":
    emitter_app = ShimaApp(emitter)
    app.register_blueprint(emitter_app)
    app.run(debug=True, host="0.0.0.0", port=2222)
