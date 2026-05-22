import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google import genai
from google.genai import types
import asyncio
import queue
import uuid
import traceback
from .state_machine import AgentStateMachine
from logger import log

load_dotenv()

class BasicAgent:
    def __init__(self, client):
        self._client = client
        self._tools = self._client.tools
        self.state_machine = AgentStateMachine(agent=self, log_callback=self._log)

        self._init_session()
        self._init_agents()
        self._init_runner()

    def _get_knowledge(self):
        knowledge_path = os.path.join(os.path.dirname(__file__), "knowledge.md")
        try:
            with open(knowledge_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _get_skills(self):
        import glob
        skills_dir = os.path.join(os.path.dirname(__file__), "skills")
        skills = "Skills\n\n"
        if os.path.exists(skills_dir):
            for skill_file in sorted(glob.glob(os.path.join(skills_dir, "*.md"))):
                with open(skill_file, "r", encoding="utf-8") as f:
                    skills += f.read() + "\n\n"
        return skills

    def _init_agents(self):
        self._root_agent = self._init_general_agent()

    def _init_general_agent(self):
        return Agent(
            name="basic_agent",
            # model="gemini-3-flash-preview",
            # model="gemini-2.5-flash",
            model="gemini-3.1-flash-lite",
            description="The main coordinator agent. Handles direct question or can delegate to subagents.",
            instruction=f"""
            You are an autonomous Minecraft agent controlling a mob in the game. You must execute the master user's orders efficiently and independently. You can use tools to interact with the game.
            
            CRITICAL AUTONOMY RULES:
            - Do NOT ask the master for permission or confirmation to take intermediate steps. 
            - If you need a tool, craft it. If you need materials, gather them. Take initiative.
            - Do NOT ask the master what to do next if you are in the middle of completing a complex task.
            - Only speak to the master when you have fully completed their request, or if you are completely and unrecoverably stuck.
            - When you're done with a request, you MUST call `transfer_to_agent` with agent_name="TaskCoordinator" to return control.
            
            Your master username is {self._client._master_username}
            
            {self._get_knowledge()}
            {self._get_skills()}
            """,
            tools=self._tools.available_methods(),
        )

    def _init_session(self):
        self._APP_NAME = "minecraft_agent_app"
        self._USER_ID = "user_1"
        self._SESSION_ID = "session_001"
        self._session_service = InMemorySessionService()
        self._session = self._session_service.create_session_sync(
            app_name=self._APP_NAME, 
            user_id=self._USER_ID, 
            session_id=self._SESSION_ID)

    def _init_runner(self):
        self._runner = Runner(agent=self._root_agent, app_name=self._APP_NAME, session_service=self._session_service)

    def _log(self, message, trace_id=None):
        log('Agent', message, trace_id)

    def _is_function_response(self, event):
        if not event.get_function_responses():
            return False
        return True
        
    def _is_there_incoming_event(self):
        return self._client.action_processor.has_incoming_agent_events()

    _TRANSIENT_ERROR_MARKERS = (
        '503', '429', 'UNAVAILABLE', 'RESOURCE_EXHAUSTED',
        'overloaded', 'high demand', 'DEADLINE_EXCEEDED',
    )
    _MAX_LLM_ATTEMPTS = 3
    _INITIAL_BACKOFF_SECONDS = 1.0

    @classmethod
    def _is_transient_llm_error(cls, error: Exception) -> bool:
        msg = str(error)
        return any(marker in msg for marker in cls._TRANSIENT_ERROR_MARKERS)

    async def call_async(self, message, trace_id) -> str:
        self._log(f'[call]: {message}', trace_id)
        content = types.Content(role='user', parts=[types.Part(text=message)])

        await self._session_service.append_event(
            self._session,
            Event(
                invocation_id=trace_id,
                author='user',
                actions=EventActions(state_delta={'trace_id': trace_id}),
            ),
        )

        backoff = self._INITIAL_BACKOFF_SECONDS
        last_error: Exception | None = None

        for attempt in range(1, self._MAX_LLM_ATTEMPTS + 1):
            final_response_text = ""
            try:
                async for event in self._runner.run_async(user_id=self._USER_ID, session_id=self._SESSION_ID, new_message=content):
                    should_break, response_text = self._handle_event(event, trace_id)
                    if response_text is not None:
                        final_response_text = response_text
                    if should_break:
                        break
                return final_response_text
            except Exception as e:
                last_error = e
                self._log(traceback.format_exc().rstrip(), trace_id)
                if self._is_transient_llm_error(e) and attempt < self._MAX_LLM_ATTEMPTS:
                    self._log(
                        f'[Retry {attempt}/{self._MAX_LLM_ATTEMPTS - 1}]: transient LLM error, sleeping {backoff:.1f}s: {str(e)}',
                        trace_id,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                break

        self._log(f'[Error]: LLM provider error or internal failure: {str(last_error)}', trace_id)
        if self.state_machine.state != self.state_machine.STATE_IDLE:
            self._log(f'[Warning]: Resetting state machine from {self.state_machine.state} to idle due to error', trace_id)
            self.state_machine.set_state(self.state_machine.STATE_IDLE)
        return f"Agent encountered an internal error: {str(last_error)}"

    def _handle_event(self, event, trace_id):
        self._debug_event(event, trace_id)

        final_response_text = None

        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"

            if event.actions and event.actions.escalate:
                return True, final_response_text

            return False, final_response_text

        return False, final_response_text


    def _debug_event(self, event, trace_id=None):
        self._log(f"[Event]: Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}", trace_id)
        if event.content and event.content.parts:
            calls = event.get_function_calls()
            for call in calls:
                tool_name = call.name
                arguments = call.args # This is usually a dictionary
                self._log(f"Tool: {tool_name}, Args: {arguments}", trace_id)
            
            responses = event.get_function_responses()
            for response in responses:
                tool_name = response.name
                response  = response.response  # This is usually a dictionary
                self._log(f"Tool: {tool_name}, response : {response}", trace_id)

            if event.content.parts[0].text:
                self._log(f"Text: {event.content.parts[0].text}", trace_id)
