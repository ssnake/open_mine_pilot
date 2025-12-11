import time

class TransportBase:
    def __init__(self):
        pass
    def on(self, event: str, *args: list, **kwargs: dict):
        pass
    def on_chat(self, message: str, *args: list, **kwargs: dict):
        pass
    def say(self, message: str):
        pass
    def run(self):
        try:
            print('run')
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass