from langgraph.graph import MessagesState
from typing import Any, Optional

class State(MessagesState):
    message: Optional[str] 
    username: Optional[str]
    llm: Any
    transport: Any