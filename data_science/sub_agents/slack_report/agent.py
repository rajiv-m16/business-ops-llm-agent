"""Reporting Agent: Formats and sends data to external services like Slack."""

import os
from google.adk.agents import LlmAgent
from google.genai import types

from .tools import send_slack_message

reporting_agent = LlmAgent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-pro"),
    name="reporting_agent",
    instruction="""
    You are an Reporting Agent. 
    Your job is to take raw data or reports and format them beautifully for Slack.
    Use bolding, bullet points, and emojis to make the data easy to read.
    ALWAYS use the `send_slack_message` tool to deliver the final formatted report.
    """,
    tools=[send_slack_message],
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
)