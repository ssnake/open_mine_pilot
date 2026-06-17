import os
import uuid
import asyncio

import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.basic_agent import BasicAgent
from tests.mocks import MockClient


def test_basic_agent_exists():
    assert BasicAgent is not None


@pytest.mark.skipif(
    not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
    reason="Set GOOGLE_API_KEY or GEMINI_API_KEY to run live agent response tests.",
)
def test_basic_agent_answers_prompt():
    session_service = InMemorySessionService()
    app_name = "mine_agent_tests"
    user_id = "test_user"
    session_id = str(uuid.uuid4())

    asyncio.run(
        session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
    )

    runner = Runner(
        app_name=app_name,
        agent=BasicAgent(MockClient())._root_agent,
        session_service=session_service,
    )

    expected_token = os.getenv("BASE_AGENT_TEST_TOKEN", "PONG_TEST_TOKEN")
    prompt = f"Reply with exactly this token somewhere in your response: {expected_token}"
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    events = list(runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ))
    
    
    assert events, "Runner returned no events."
    final_texts = []
    for event in events:
        assert not event.error_code, f"Agent returned error: {event.error_code} {event.error_message}"
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    final_texts.append(part.text)

    response_text = " ".join(final_texts).strip()
    assert response_text, "Expected non-empty final response text."
    assert expected_token in response_text
