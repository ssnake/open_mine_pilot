from google.adk.agents import LlmAgent

base_agent = LlmAgent(
    name="test_agent",
    model="gemini-2.5-flash",
    description="Agent to answer questions about anything.",
    instruction="You are a helpful test agent who can answer user questions about anything",
)
