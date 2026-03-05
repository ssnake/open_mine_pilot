import uuid

class Base:
    def __init__(self, client):
        self._client = client
        self._bot = client._bot
        self._handlers = []
    
    def _log(self, message, trace_id: str = None):
        if trace_id:
            print(f"[{self.__class__.__name__}][{trace_id}]: {message}")
        else:
            print(f"[{self.__class__.__name__}]: {message}")
    
    def bind(self):
        pass

    def trace_id(self) -> str:
        return str(uuid.uuid4())