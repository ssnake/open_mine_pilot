from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    def __init__(self, bot):
        self._bot = bot
        self._tools = bot.tools 
        self._init_agents()
        self._init_session()
        self._init_runner()    

    def call(self, message, role='user'):
        self._log(f'{role}: {message}')
        final_response_text = "Agent did not produce a final response." # Default
        content = types.Content(role=role, parts=[types.Part(text=message)])
        
        for event in self._runner.run(user_id=self._USER_ID, session_id=self._SESSION_ID, new_message=content):
            self._log(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")
            if event.is_final_response():          
                if event.content and event.content.parts:
                    # Assuming text response in the first part
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break # Stop processing events once the final response is found

        return final_response_text

    def _init_agents(self):
        self._root_agent = Agent(
            name="main_minecraft_agent",
            model="gemini-2.5-flash",
            description="The main coordinator agent. Handles direct question or can delegate to subagents.",
            instruction="You are a minecraft agent control a mob in the game. You must execute the user's orders. You can use tools to interact with the game. Async tools should be final responses. There are rols: user, agent, mob. User is a player, agent is you, mob is a mob you control. You are agent.",
            tools=[
                self._tools.get_my_position,
                self._tools.goto_position
            ],
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

    def _log(self, message):
        print(f'[{self._APP_NAME}]: {message}')
        
