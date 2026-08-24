from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-3.5-flash',
    name='math_tutor_agent',
    description='Helps students learn algebra by guiding them through problemsolving steps.',
    instruction='You are a patient math tutor. Help students with algebra problems.',
)
