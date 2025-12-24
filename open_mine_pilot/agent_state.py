from langgraph.graph import MessagesState

class State(MessagesState):
    user_query: Optional[str] # The user's original query