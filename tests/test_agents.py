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

"""Test cases for the Business Operations orchestrator and its sub-agents."""

import os
import sys
import unittest

import pytest
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import the new architecture
from data_science.agent import root_agent
from data_science.sub_agents.hr.agent import hr_agent
from data_science.sub_agents.sales.agent import sales_agent

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()


class TestAgents(unittest.IsolatedAsyncioTestCase):
    """Test cases for the Business Operations Multi-Agent system."""

    async def asyncSetUp(self):
        """Set up for test methods."""
        super().setUp()
        self.session = await session_service.create_session(
            app_name="DataAgent",
            user_id="test_user",
        )
        self.user_id = "test_user"
        self.session_id = self.session.id

        # Removed Runner initialization from here

    def _run_agent(self, agent, query):
        """Helper method to run an agent and get the final response."""
        
        # Instantiate the Runner HERE with the actual agent
        runner = Runner(
            app_name="DataAgent",
            agent=agent,
            artifact_service=artifact_service,
            session_service=session_service,
        )
        
        content = types.Content(role="user", parts=[types.Part(text=query)])
        
        events = list(
            runner.run(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=content,
            )
        )

        last_event = events[-1]
        final_response = "".join(
            [part.text for part in last_event.content.parts if part.text]
        )
        return final_response

    # --- 1. DIRECT SUB-AGENT TESTS ---

    @pytest.mark.hr
    async def test_hr_agent_directly(self):
        """Test the HR agent's ability to handle employee/bench queries directly."""
        query = "How many employees do we have on the bench?"
        response = self._run_agent(hr_agent, query)
        print(f"\n[HR Agent Direct] Response:\n{response}")
        self.assertIsNotNone(response)

    @pytest.mark.sales
    async def test_sales_agent_directly(self):
        """Test the Sales agent's ability to handle revenue/product queries directly."""
        query = "What is our total sales revenue?"
        response = self._run_agent(sales_agent, query)
        print(f"\n[Sales Agent Direct] Response:\n{response}")
        self.assertIsNotNone(response)

    # --- 2. ORCHESTRATOR ROUTING TESTS ---

    @pytest.mark.orchestrator
    async def test_root_agent_routing_to_hr(self):
        """Test that the orchestrator properly routes to HR."""
        query = "Can you pull the list of developers currently on the bench?"
        response = self._run_agent(root_agent, query)
        print(f"\n[Root Agent -> HR] Response:\n{response}")
        self.assertIsNotNone(response)

    @pytest.mark.orchestrator
    async def test_root_agent_routing_to_sales(self):
        """Test that the orchestrator properly routes to Sales."""
        query = "Which product category has the highest profit margin?"
        response = self._run_agent(root_agent, query)
        print(f"\n[Root Agent -> Sales] Response:\n{response}")
        self.assertIsNotNone(response)

    # --- 3. CROSS-DOMAIN TEST ---

    @pytest.mark.orchestrator
    async def test_root_agent_cross_domain_synthesis(self):
        """Test that the orchestrator can synthesize answers from BOTH domains."""
        query = "How many employees are currently on the bench, and what is our total sales revenue?"
        response = self._run_agent(root_agent, query)
        print(f"\n[Root Agent Cross-Domain] Response:\n{response}")
        
        # A successful cross-domain response should mention both topics
        self.assertIsNotNone(response)
        response_lower = response.lower()
        self.assertTrue("bench" in response_lower or "employee" in response_lower, "Failed to fetch HR data.")
        self.assertTrue("sale" in response_lower or "revenue" in response_lower, "Failed to fetch Sales data.")


if __name__ == "__main__":
    unittest.main()