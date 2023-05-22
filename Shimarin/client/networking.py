import aiohttp
import json
import typing


class Response:
    def __init__(self, status_code, content):
        self.status = status_code
        self.content = content

    async def json(self):
        return json.loads(self.content.decode("utf-8"))


async def send_get_request(session: aiohttp.ClientSession, *args, **kwargs) -> Response:
    """
    Function to send a rest request and return the Response
    :session A client session object from aiohttp
    :param *args and *kwargs to be used on the request
    :return a Response object with the content of the endpoint
    """
    response: typing.Union[Response, None] = None
    async with session.request("GET", *args, **kwargs) as resp:
        response = Response(resp.status, await resp.read())
    return response


async def send_post_request(
    session: aiohttp.ClientSession, *args, **kwargs
) -> Response:
    """
    Function to send a rest request and return the Response
    :session A client session object from aiohttp
    :param *args and *kwargs to be used on the request
    :return a Response object with the content of the endpoint
    """
    response: typing.Union[Response, None] = None
    async with session.request("POST", *args, **kwargs) as resp:
        response = Response(resp.status, await resp.read())
    return response
