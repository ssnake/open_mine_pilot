from .agent_orchestrator import AgentOrchestrator
from llm_agents import create_task_coordinator, ComplexAgent


class MultiAgentOrchestrator(AgentOrchestrator):
    def _init_agents(self):
        complex_agent = self._init_complex_agent()

        self._root_agent = create_task_coordinator(
            model=self._default_model(),
            sub_agents=[complex_agent],
        )

    def _init_complex_agent(self):
        return ComplexAgent(
            model=self._default_model(),
            orchestrator=self,
            log_callback=self._log)
