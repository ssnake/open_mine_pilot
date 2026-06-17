from google.adk.agents import Agent


def create_general_agent(*, model: str, orchestrator) -> Agent:
    return Agent(
        name="basic_agent",
        model=model,
        description="The main coordinator agent. Handles direct question or can delegate to subagents.",
        instruction=f"""
            You are an autonomous Minecraft agent controlling a mob in the game. You must execute the master user's orders efficiently and independently. You can use tools to interact with the game.

            CRITICAL AUTONOMY RULES:
            - Do NOT ask the master for permission or confirmation to take intermediate steps.
            - If you need a tool, craft it. If you need materials, gather them. Take initiative.
            - Do NOT ask the master what to do next if you are in the middle of completing a complex task.
            - Only speak to the master when you have fully completed their request, or if you are completely and unrecoverably stuck.
            - When you're done with a request, you MUST call `transfer_to_agent` with agent_name="TaskCoordinator" to return control.

            Your master username is {orchestrator._client._master_username}

            {orchestrator._get_knowledge()}
            {orchestrator._get_skills()}
            """,
        tools=orchestrator._tools.available_methods(),
    )
