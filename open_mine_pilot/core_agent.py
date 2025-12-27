from typing import Optional
from .agent_state import State
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from .agent_graph import build_graph


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
        self._app = build_graph()

    def run(self, username: str, message: str) -> str:
        """Run the agent on a single chat message and return the reply text.

        The agent receives the player name and their message.
        """
        self._app.invoke({
            "username": username, 
            "message": message,
            "llm": _reasoning_llm
        })