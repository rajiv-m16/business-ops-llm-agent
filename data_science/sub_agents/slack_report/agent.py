
import os
from google.adk.agents import LlmAgent
from google.genai import types

from .tools import send_slack_message

from .prompts import return_instructions_reporting

reporting_agent = LlmAgent(
    model=os.getenv("SLACK_AGENT_MODEL", "gemini-2.5-flash-lite"),
    name="reporting_agent",
    instruction=return_instructions_reporting(),  
    tools=[send_slack_message],
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
)