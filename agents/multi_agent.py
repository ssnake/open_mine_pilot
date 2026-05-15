from .basic_agent import BasicAgent
from google.adk.agents import LlmAgent
from .complex_agent import ComplexAgent
# from google.adk.tools.tool_context import ToolContext

  

class MultiAgent(BasicAgent):
    def _default_model(self) -> str:
        return 'gemini-3.1-flash-lite'
    
    def _init_agents(self):
        complex_agent = self._init_complex_agent()

        self._root_agent =LlmAgent(
            name="TaskCoordinator",
            model=self._default_model(),
            instruction="""
            You're a task coordinator inside minecraft game. Route user requests to appropriate sub-agent.

            Only send user-facing text when it is necessary:
            - answer direct questions
            - report that a task is completed when a short confirmation is useful
            - report unrecoverable errors or when you are stuck

            Do not repeat internal plans, intermediate reasoning, or tool activity.
            If a sub-agent can handle the request, transfer control to it.
            If no user-facing message is needed, return an empty response.
            """,
            description="Main task coordinator.",
            sub_agents=[complex_agent])
    
    def _init_complex_agent(self):
        return ComplexAgent(
            model=self._default_model(),
            client=self._client,
            tools=self._tools,
            knowledge=self._get_knowledge(),
            skills=self._get_skills(),
            log_callback=self._log)


