from .transport_base import TransportBase

class Transport(TransportBase):
    def __init__(self, username: str):
        self._username = username

    def on_chat(self, username: str, message: str):
        if self._username == username:
            return
        print(f'{username} said: {message}')
        self.say(f'Hello {username}')
        