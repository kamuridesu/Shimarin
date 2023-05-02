import os


class Config:
    def __init__(self, server_endpoint: str) -> None:
        self.SERVER_ENDPOINT = server_endpoint


config = Config(os.getenv("SERVER_ENDPOINT"))
