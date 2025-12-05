from abc import ABC, abstractmethod


class BaseBot(ABC):
    def __init__(self, host: str, port: int, username: str):
        self.host = host
        self.port = port
        self.username = username

    @abstractmethod
    def on(self, event: str, handler):
        ...

    @abstractmethod
    def chat(self, message: str):
        ...

    @abstractmethod
    def run(self):
        ...
