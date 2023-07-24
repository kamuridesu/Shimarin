import json

from Shimarin.plugins.flask_api import app, emitter
from Shimarin.server.events import Event, EventAnswerTimeoutError

from flask import request


async def handle_test(params: dict = {}):
    event = Event("update", json.dumps(params), json.loads)
    await emitter.send(event)
    print("waiting for answer")
    try:
        return await event.get_answer(60)  # 1 minute timeout
    except EventAnswerTimeoutError:
        return "fail"


@app.route("/test", methods=["GET"])
async def test_route():
    args = request.get_json(force=True, silent=True)
    if args is None:
        args = {}
    return await handle_test(args)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=2222)
