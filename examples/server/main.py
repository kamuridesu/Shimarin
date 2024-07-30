import json

import sys
sys.path.insert(0, "/home/kamuri/Documents/Personal/shimarin")

from Shimarin.plugins.flask_api import FlaskApp
from Shimarin.server.events import Event, EventEmitter
from Shimarin.server.exceptions import EventAnswerTimeoutError
from Shimarin.plugins.middleware.sqlite_middleware import SQLitePersistenceMiddleware

from flask import request, Flask


app = Flask("server")
emitter = EventEmitter(persistence_middleware=SQLitePersistenceMiddleware("test.db"))
# emitter =EventEmitter()


async def handle_test(params: dict = {}):
    event = Event("update", json.dumps(params), json.loads)
    await emitter.send(event)
    print("waiting for answer")
    try:
        return (await emitter.get_answer(event.identifier, timeout = 60))  # 1 minute timeout
    except EventAnswerTimeoutError:
        return "fail"


@app.route("/test", methods=["GET"])
async def test_route():
    args = request.get_json(force=True, silent=True)
    if args is None:
        args = {}
    return await handle_test(args)


if __name__ == "__main__":
    emitter_app = FlaskApp(emitter)
    app.register_blueprint(emitter_app.blueprint)
    app.run(debug=True, host="0.0.0.0", port=2222)
    app.run(debug=True, host="0.0.0.0", port=2222)
