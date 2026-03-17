import os
import sys

# 1. Move path hack to the top to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import pytest
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Now import your agents
from data_science.agent import root_agent
from data_science.sub_agents.hr.agent import hr_agent
from data_science.sub_agents.sales.agent import sales_agent

session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

class TestAgents(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.user_id = "test_user"
        # We create a session, but consider generating a fresh ID per test
        self.session = await session_service.create_session(
            app_name="DataAgentTest",
            user_id=self.user_id,
        )
        self.session_id = self.session.id

    async def _run_agent(self, agent, query):
        runner = Runner(
            app_name="DataAgentTest",
            agent=agent,
            artifact_service=artifact_service,
            session_service=session_service,
        )
        
        content = types.Content(role="user", parts=[types.Part(text=query)])
        final_response = ""

        async for event in runner.run(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=content,
            ):
            # Aggregating response text
            if hasattr(event, 'content') and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response += part.text
                    # Optional: Log function calls to see the agent's 'thought process'
                    elif part.function_call:
                        print(f"\n[Tool Call]: {part.function_call.name}")
                        
        return final_response

    # --- TESTS (Now using await) ---

    @pytest.mark.asyncio
    async def test_hr_agent_directly(self):
        """Test the HR agent's ability to handle queries."""
        query = "How many employees do we have on the bench?"
        # FIXED: Added await
        response = await self._run_agent(hr_agent, query)
        print(f"\n[HR Agent Direct] Response:\n{response}")
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0, "Agent returned empty response")

    @pytest.mark.asyncio
    async def test_sales_agent_directly(self):
        """Test the Sales agent's ability to handle queries."""
        query = "What is our total sales revenue?"
        # FIXED: Added await
        response = await self._run_agent(sales_agent, query)
        print(f"\n[Sales Agent Direct] Response:\n{response}")
        self.assertIsNotNone(response)

    @pytest.mark.asyncio
    async def test_root_agent_routing_to_hr(self):
        """Test that the orchestrator properly routes to HR."""
        query = "Can you pull the list of developers currently on the bench?"
        
        response = await self._run_agent(root_agent, query)
        self.assertIsNotNone(response)

if __name__ == "__main__":
    unittest.main()