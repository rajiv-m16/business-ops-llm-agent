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



# Copyright 2025 Google LLC
# [License omitted for brevity]

"""Top level agent for data agent multi-agents."""

import json
import logging
import os
import importlib.resources

from google.adk.agents import LlmAgent
from google.genai import types

from .prompts import return_instructions_root


from .tools import call_hr_agent, call_sales_agent, call_reporting_agent

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

_dataset_config = {}

def load_dataset_config():
    """Load the dataset configurations for the agent from the config file"""
    dataset_config_file = os.getenv("DATASET_CONFIG_FILE", "master_config.json")
    filename_only = os.path.basename(dataset_config_file)
    dataset_config = None
    
    try:
        config_text = importlib.resources.read_text("data_science", filename_only)
        dataset_config = json.loads(config_text)
    except Exception:
        pass
        
    if dataset_config is None:
        possible_paths = [dataset_config_file, f"data_science/{filename_only}", f"./{filename_only}"]
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    dataset_config = json.load(f)
                break

    if dataset_config is None:
        raise FileNotFoundError(f"CRITICAL: Could not find dataset config file: {dataset_config_file}")

    return dataset_config

def get_dataset_definitions_for_instructions() -> str:
    """Returns the dataset definitions instructions block WITHOUT heavy schemas"""
    dataset_definitions = "\n<DATASETS>\n"
    
    for dataset in _dataset_config["datasets"]:
        dataset_name = dataset["name"]
        
        dataset_definitions += f"""
<{dataset_name.upper()}>
<DESCRIPTION>
{dataset["description"]}
</DESCRIPTION>
</{dataset_name.upper()}>
"""
        
    dataset_definitions += "</DATASETS>\n"
    return dataset_definitions

def get_root_agent() -> LlmAgent:
    tools = []
    
    for dataset in _dataset_config["datasets"]:
        if dataset["name"] == "people_analytics":
            tools.append(call_hr_agent)
        elif dataset["name"] == "sales_and_customers":
            tools.append(call_sales_agent)

    agent = LlmAgent(
        model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-pro"),
        name="data_science_root_agent",
        instruction=return_instructions_root() + get_dataset_definitions_for_instructions(),
        tools=tools + [call_reporting_agent], 
        generate_content_config=types.GenerateContentConfig(temperature=0.01),
    )
    return agent

_dataset_config = load_dataset_config()
root_agent = get_root_agent()



















