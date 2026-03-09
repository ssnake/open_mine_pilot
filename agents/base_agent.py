import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google import genai
from google.genai import types
import asyncio
import queue
import uuid
import traceback
from .state_machine import AgentStateMachine

load_dotenv()

class BaseAgent:
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
        knowledge = self._get_knowledge()
        skills = self._get_skills()

        self._root_agent = Agent(
            name="main_minecraft_agent",
            # model="gemini-3-flash-preview",
            # model="gemini-2.5-flash",
            model="gemini-3.1-flash-lite-preview",
            description="The main coordinator agent. Handles direct question or can delegate to subagents.",
            instruction=f"""
            You are an autonomous Minecraft agent controlling a mob in the game. You must execute the master user's orders efficiently and independently. You can use tools to interact with the game.
            
            CRITICAL AUTONOMY RULES:
            - Do NOT ask the master for permission or confirmation to take intermediate steps. 
            - If you need a tool, craft it. If you need materials, gather them. Take initiative.
            - Do NOT ask the master what to do next if you are in the middle of completing a complex task.
            - Only speak to the master when you have fully completed their request, or if you are completely and unrecoverably stuck.
            
            Your master username is {self._client._master_username}
            
            {knowledge}
            {skills}
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
        print(f'[Agent]:{trace_id} {message}')

    def _is_function_response(self, event):
        if not event.get_function_responses():
            return False
        return True
        
    def _is_async_function_successful_response(self, event):
        if not event.get_function_responses():
            return False

        response = event.get_function_responses()[0]
        name = response.name
        response  = response.response
        return name.startswith('async_') and response.get("status") == "success"
        
    def _is_there_incoming_event(self):
        return self._client.action_processor.has_incoming_agent_events()

    async def call_async(self, message, trace_id) -> str:
        self._log(f'[call]: {message}', trace_id)
        final_response_text = ""
        content = types.Content(role='user', parts=[types.Part(text=message)])
        
        try:
            async for event in self._runner.run_async(user_id=self._USER_ID, session_id=self._SESSION_ID, new_message=content):
                self._debug_event(event, trace_id)

                if event.is_final_response():          
                    if event.content and event.content.parts:
                        # Assuming text response in the first part
                        final_response_text = event.content.parts[0].text
                    elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                        final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                    break # Stop processing events once the final response is found

                if self._is_async_function_successful_response(event):
                    self._log(f'[call]: Async function success response received', trace_id)
                    break
        except Exception as e:
            self._log(f'[Error]: LLM provider error or internal failure: {str(e)}', trace_id)
            # You can also use traceback.print_exc() if you need more details in the logs.
            if self.state_machine.state != self.state_machine.STATE_IDLE:
                self._log(f'[Warning]: Resetting state machine from {self.state_machine.state} to idle due to error', trace_id)
                self.state_machine.set_state(self.state_machine.STATE_IDLE)
            final_response_text = f"Agent encountered an internal error: {str(e)}"

        return final_response_text      

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
