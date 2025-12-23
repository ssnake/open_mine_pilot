import time

class Transport:
    def __init__(self, username: str):
        self._username = username

    def on_chat(self, username: str, message: str):
        if self._username == username:
            return
        print(f'{username} said: {message}')
        self.say(f'Hello {username}')
        
    def on_end(self, reason: str):
        print(f'Connection ended: {reason}')
    def on_error(self, error: str):
        print(f'Connection error: {error}')
    def on_spawn(self):
        print(f'{self._username} spawned')
    def on_login(self):
        print(f'{self._username} logged in')
    def on_unable_to_connect(self, reason: str):
        print(f'Unable to connect: {reason}')

    def say(self, message: str):
        pass

    def run(self):
        try:
            print('run')
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass