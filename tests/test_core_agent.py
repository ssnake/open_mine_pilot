import pytest
from open_mine_pilot import CoreAgent, build_graph, State
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from tests.mock_transport import MockTransport
from langgraph.types import Command

load_dotenv()

llm = ChatOpenAI(
            model="o3",
            model_kwargs={"response_format": {"type": "json_object"}},
        )
transport = MockTransport()

def test_agent_node_execution() -> None:
    checkpointer = MemorySaver()
    
    graph = build_graph()
    node = graph.nodes["agent"]
    result = node.invoke(
        State(
            username="test_user", 
            message="test_message",
            llm=llm,
            transport=transport
        )
    )
    assert isinstance(result, Command) and result.goto == "echo"