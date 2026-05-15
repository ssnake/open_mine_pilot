from google.adk.agents import LoopAgent, LlmAgent, Agent
from google.adk.agents import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator, ClassVar

class ComplexAgent(Agent):
    """
    Agent for handling complex tasks that require multiple steps and planning.
    """
    planner_agent: LlmAgent
    action_agent: LlmAgent
    loop_agent: LoopAgent
    log_callback: callable
    COMPLETION_PHRASE: ClassVar[str] = 'ALL IS DONE'

    def __init__(self,
                model: str,
                client,
                tools,
                knowledge: str,
                skills: str,
                log_callback=None):
        planner_agent = self._init_planner_agent(model, client, knowledge, skills)
        action_agent = self._init_action_agent(model, tools)
        loop_agent = LoopAgent(
            name='PlannerActionLoop',
            sub_agents=[planner_agent, action_agent],
            max_iterations=2)
        
        super().__init__(
            name='ComplexAgent',
            planner_agent=planner_agent,
            action_agent=action_agent,
            loop_agent=loop_agent,
            sub_agents=[loop_agent],
            log_callback=log_callback
            )

    def _init_planner_agent(self, model: str, client, knowledge: str, skills: str) -> LlmAgent:
        return LlmAgent(
            name='PlannerAgent',
            description='Planner agent for complex task planning',
            model='gemini-3.1-pro-preview',
            instruction=f"""
            You are a planner agent. You're part of a bigger agent system that can execute tasks in Minecraft.
            You should plan complex tasks for delegating them to other agents.
            Write a plan in markdown format with checboxes for given user request. For example:
            User asked: "Log a oak logs"
            You should write:
             ```markdown
             # Plan
             [x] Check if you're equipped with a axe
             [ ] check if you have enough resource to craft a axe
             [ ] Find a oak tree to mine logs for axe
             [ ] Log a oak logs
             [ ] Craft a axe
             [ ] Equip a axe
             [ ] find oak trees
             [ ] mine oak logs
             [ ] collect oak logs
             [ ] inform user when task is completed
             ```
            Your master username is {client._master_username}

            Here is updated plan from previous iteration. 
            Steps that are already done are marked with [x]. Step that are not yet done are marked with [ ].
            If you see step with [!], it means that step failed. You should try to fix it:
            ```
            {{updated_plan?}}
            ```

            {knowledge}
            {skills}

            You must return only plan.
            """,
            output_key='plan')

    def _init_action_agent(self, model: str, tools) -> LlmAgent:
        return LlmAgent(
            name='ActionAgent',
            description='Action agent for executing tasks',
            model=model,
            instruction=f"""
            You are an action agent. You're part of a bigger agent system that can execute tasks in Minecraft.
            You should execute tasks based on the plan provided by the planner agent.
            Here is plan. Tasks that should be done is marked with [ ]:
            {{plan}}

            Once you complete a task, mark it with [x].
            If you encounter an error, mark the task with [!] and explain the error after original text and return control to planner. For example:
            ```
            [!] Craft a axe: I don't have enough resources
            ```

            You must return updated plan if the plan is not finished. 
            If the plan has completed all tasks and no user-facing reply is needed, return exactly "{self.COMPLETION_PHRASE}".
            If the plan has completed all tasks and a user-facing reply is necessary, return a short user-facing message followed by "{self.COMPLETION_PHRASE}".
            Never include the plan in the completion response.

            """,
            tools=tools.available_methods(),
            output_key='updated_plan')

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        trace_id = ctx.session.state.get('trace_id', None)
        if self.log_callback:
            self.log_callback(f'[{self.name}] started', trace_id)

        await ctx.session_service.append_event(
            ctx.session,
            Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                actions=EventActions(
                    state_delta={'plan': None, 'updated_plan': None},
                    agent_state={'status': 'running'},
                ),
            ),
        )

        async for event in self.loop_agent.run_async(ctx):      
            if event.content and event.content.parts:
                part_texts = [part.text for part in event.content.parts if getattr(part, 'text', None)]
                if any(self.COMPLETION_PHRASE in part_text for part_text in part_texts):
                    self.log_callback(f'[{self.name}] Completion phrase detected, stopping', trace_id)
                    self.log_callback(f"[{self.name}] Event: {event.model_dump_json(indent=2, exclude_none=True)}", trace_id)
                    await ctx.session_service.append_event(
                        ctx.session,
                        Event(
                            invocation_id=ctx.invocation_id,
                            author=self.name,
                            actions=EventActions(end_of_agent=True),
                        ),
                    )
                    break
            yield event
