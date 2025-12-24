from typing import Optional
from .agent_state import State
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition



def agent_node(state: State) -> Command[Literal["echo", "agent"]]:
    """Agent node that decides when to call tools based on chat."""
    return state

def echo_node(state: State) -> State:
    """Tools node that calls tools based on chat."""
    return state

class CoreAgent:
    """Core agent responsible for deciding when to call tools based on chat.

    The agent is implemented as a LangGraph graph with:
    - an LLM node (OpenAI chat model)
    - a tool node exposing the "echo_tool"

    The public entry point is the "run" method which returns a response
    that can be sent back to the Minecraft chat.
    """

    def __init__(self, system_prompt: Optional[str] = None, model: str = "o3"):
        self._system_prompt = system_prompt or (
            "You are an in-game assistant for Minecraft. "
            "When a player says something that should be repeated back to them, "
            "you MUST use the `echo_tool` to echo the message. "
            "Use tools whenever they are appropriate."
        )

        _reasoning_llm = ChatOpenAI(
            model="o3",
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        graph = StateGraph(State)
        graph.add_node("agent", agent_node)
        graph.add_node("echo", echo_node)
        graph.add_edge("echo", "agent")
        graph.add_edge(StateGraph.START, "agent")
        self._app = graph.compile()

    def run(self, username: str, message: str) -> str:
        """Run the agent on a single chat message and return the reply text.

        The agent receives the player name and their message and decides
        whether to use tools (e.g. echo_tool) or answer directly.
        """
        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=f"Player {username} said: {message}"),
        ]

        result = self._app.invoke({"messages": messages})
        output_messages = result.get("messages", [])

        ai_messages = [m for m in output_messages if isinstance(m, AIMessage)]
        if not ai_messages:
            return ""

        return ai_messages[-1].content or ""
