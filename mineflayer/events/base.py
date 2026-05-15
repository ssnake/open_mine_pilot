import uuid
from logger import log

class Base:
    def __init__(self, client):
        self._client = client
        self._bot = client._bot
        self._handlers = []

    def _log(self, message, trace_id: str = None):
        log(self.__class__.__name__, message, trace_id)
    
    def bind(self):
        pass

    def trace_id(self) -> str:
        return str(uuid.uuid4())