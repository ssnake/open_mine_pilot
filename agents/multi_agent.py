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
            instruction="You're a task coordinator inside minecraft game. Route user requests to appropriate sub-agent.",
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


