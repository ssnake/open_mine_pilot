
from open_mine_pilot.transport import Transport

class MockTransport(Transport):
    def __init__(self):
        super().__init__("test")
    def say(self, message: str):
        print(message)