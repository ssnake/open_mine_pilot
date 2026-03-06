from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv
import asyncio
import threading
import queue
import uuid
import traceback
from .state_machine import AgentStateMachine

load_dotenv()

class BaseAgent:
    def __init__(self, client):
        self._client = client
        self._task_queue = queue.Queue()
        self._tools = self._client.tools
        self.state_machine = AgentStateMachine(agent=self, log_callback=self._log)

        self._init_session()
        self._init_agents()
        self._init_runner()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while True:
            try:
                task = self._task_queue.get()
                if task is None:
                    break

                task_type, args = task
                if task_type == 'chat':
                    self._handle_chat(*args)
                elif task_type == 'system_event':
                    self._handle_system_event(*args)
            except Exception as e:
                self._log(f"Error processing task: {e}")
            finally:
                self._task_queue.task_done()

    def enqueue_chat(self, message: str, trace_id: str):
        self._task_queue.put(('chat', (message, trace_id)))

    def enqueue_system_event(self, event_name: str, message: str, trace_id: str):
        self._task_queue.put(('system_event', (event_name, message, trace_id)))

    def _handle_chat(self, message: str, trace_id: str):
        result = self.call(message, trace_id)
        if result:
            self._client.whisper(self._client._master_username, result)

    def _handle_system_event(self, event_name: str, message: str, trace_id: str):
        # Filter events based on current state using the state machine
        if not self.state_machine.filter_event(event_name, trace_id):
            return
        
        formatted_message = f"[SYSTEM EVENT: {event_name}] {message}"
        result = self.call(formatted_message, trace_id)
        if result:
            self._client.whisper(self._client._master_username, result)

    def _init_agents(self):
        knowledge = """
        Knowledge about the Minecraft world:
        - Items and blocks in Minecraft are usually prefixed with 'minecraft:'. For example: 'minecraft:diamond_helmet', 'minecraft:iron_pickaxe', 'minecraft:dirt', etc.
        - When looking for a generic block type like "any log", you should provide all variations to `find_blocks` (e.g. `['oak_log', 'birch_log', 'spruce_log', 'jungle_log', 'acacia_log', 'dark_oak_log', 'mangrove_log', 'cherry_log']`).
        - Tool call that are waiting for event response must be with "finishReason": "STOP"
        - You must use only one tool call at a time.
        - Do not call another tool until you receive a response from the current tool.
        - When async tool is called do not call another tool
        
        """

        skills = """
        Skills 

        1. Mine a block
          - make sure following is stopped before start
          - Tools must be called sequentially, one at a time. Call a tool, wait for its result, and only then proceed to the next step.
          - To mine a block, first use `find_blocks` to locate nearby blocks of the desired type.
          - Memorize block name
          - Use `goto_position` to navigate to the block's location. Wait until you receive `[SYSTEM EVENT: pathfinding_result]` before proceeding.
          - Once reached, use `start_dig` to begin mining the block.
          - Mining is an asynchronous process. It is considered finished when you receive a game update event of either `diggingCompleted` or `diggingAborted`.
          - When block is finished make sure you mined correct block name
        2. Pathing
          - make sure following is stopped before start
          - if you need to get any position use `async_goto_position`
          - if you stuck, call `async_stop_pathing` first
          - if you stuck again, go to random position around you
        3. Event Timeouts
          - if an expected asynchronous event takes longer than 60 seconds, you will receive `[SYSTEM EVENT: state_timeout]`
          - if you receive a timeout, you should evaluate your current situation and retry the action, try a different action, or report the issue to the user.
        """
        self._root_agent = Agent(
            name="main_minecraft_agent",
            # model="gemini-3-flash-preview",
            model="gemini-2.5-flash",
            # model="gemini-3.1-flash-lite-preview",
            description="The main coordinator agent. Handles direct question or can delegate to subagents.",
            instruction=f"""
            You are a minecraft agent control a mob in the game. You must execute the master user's orders. You can use tools to interact with the game.
            
            You master username is {self._client._master_username}
            
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
        
    def _is_async_function_successful_response(self, event):
        if not event.get_function_responses():
            return False

        response = event.get_function_responses()[0]
        name = response.name
        response  = response.response
        return name.startswith('async_') and response.get("status") == "success"
        
    def _is_there_incoming_event(self, event):
        return not self._task_queue.empty() and self._is_function_response(event)

    def call(self, message, trace_id) -> str:
        self._log(f'[call]: {message}', trace_id)
        final_response_text = ""
        content = types.Content(role='user', parts=[types.Part(text=message)])
        for event in self._runner.run(user_id=self._USER_ID, session_id=self._SESSION_ID, new_message=content):
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

            if self._is_there_incoming_event(event):
                self._log(f'[call]: There are incoming events, breaking', trace_id)
                break

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
