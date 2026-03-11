# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



"""Tools for the Orchestrator Agent."""

import logging
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

# Import your newly created sub-agents
from .sub_agents.hr.agent import hr_agent
from .sub_agents.sales.agent import sales_agent

logger = logging.getLogger(__name__)

async def call_hr_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call the HR database (nl2sql) agent."""
    logger.debug("call_hr_agent: %s", question)
    agent_tool = AgentTool(agent=hr_agent)
    hr_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["hr_agent_output"] = hr_agent_output
    return hr_agent_output


async def call_sales_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call the Sales database (nl2sql) agent."""
    logger.debug("call_sales_agent: %s", question)
    agent_tool = AgentTool(agent=sales_agent)
    sales_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["sales_agent_output"] = sales_agent_output
    return sales_agent_output











# Add this to your imports at the top:
from .sub_agents.slack_report.agent import reporting_agent

# ... existing code ...

async def call_reporting_agent(
    message: str,
    tool_context: ToolContext,
):
    """Tool to format and send a report via Slack."""
    logger.debug("call_reporting_agent triggered.")
    agent_tool = AgentTool(agent=reporting_agent)
    
    # We pass the message we want sent as the "request" to the sub-agent
    reporting_agent_output = await agent_tool.run_async(
        args={"request": f"Format this data and send it to Slack: {message}"}, 
        tool_context=tool_context
    )
    tool_context.state["reporting_agent_output"] = reporting_agent_output
    return reporting_agent_output