from open_mine_pilot.agent_state import State
from langgraph.graph import StateGraph
from langgraph.types import Command
from langgraph.graph import START
import json
from typing import Literal

def agent_node(state: State) -> Command[Literal["echo", "agent"]]:
    """Agent node that decides when to call tools based on chat."""
    prompt = f"""
    You are an in-game assistant for Minecraft.
    You are given a chat message from a player and you must decide
    if you should use the `echo_tool` to echo the message.
    Output a JSON object with the following format:
    {{
        "goto": "echo" | "agent",
    }}
    Player {state.get("username")} said: {state.get("message")}
    """
    result = state.get("llm").invoke(prompt)
    content_str = result.content if isinstance(result.content, str) else str(result.content)
    parsed = json.loads(content_str)
    return Command(goto=parsed["goto"])

def echo_node(state: State) -> State:
    """Tools node that calls tools based on chat."""
    state.get("transport").say(state.get("message"))
    return state

def build_graph():
    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_node("echo", echo_node)
    graph.add_edge("echo", "agent")
    graph.add_edge(START, "agent")
    return graph.compile()