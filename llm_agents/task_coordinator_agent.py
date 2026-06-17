from google.adk.agents import LlmAgent


def create_task_coordinator(*, model: str, sub_agents: list) -> LlmAgent:
    return LlmAgent(
        name="TaskCoordinator",
        model=model,
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
        sub_agents=sub_agents,
    )
