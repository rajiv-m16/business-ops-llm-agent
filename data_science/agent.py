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
    dataset_definitions = "\n<DATASETS>\n"
    for dataset in _dataset_config["datasets"]:
        dataset_name = dataset["name"]
        dataset_definitions += f"<{dataset_name.upper()}>\n<DESCRIPTION>\n{dataset['description']}\n</DESCRIPTION>\n</{dataset_name.upper()}>\n"
    dataset_definitions += "</DATASETS>\n"
    return dataset_definitions

# --- RBAC IMPLEMENTATION ---
def get_root_agent(user_role: str = "viewer") -> LlmAgent:
    """
    Initializes the agent with tools restricted by user role.
    Roles: 'admin' (all), 'hr_manager' (HR only), 'sales_lead' (Sales only)
    """
    # 1. Define Role Permissions
    role_permissions = {
        "admin": [call_hr_agent, call_sales_agent, call_reporting_agent],
        "hr_manager": [call_hr_agent, call_reporting_agent],
        "sales_lead": [call_sales_agent, call_reporting_agent],
        "viewer": [] # Viewers have no tools, they can only chat with the model
    }
    
    # 2. Filter tools based on role
    allowed_tools = role_permissions.get(user_role, [])
    
    # 3. Create instruction with role context
    full_instruction = f"USER_ROLE: {user_role}\n" + return_instructions_root() + get_dataset_definitions_for_instructions()

    return LlmAgent(
        model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-flash"),
        name="data_science_root_agent",
        instruction=full_instruction,
        tools=allowed_tools, 
        generate_content_config=types.GenerateContentConfig(temperature=0.01),
    )



# Load config
_dataset_config = load_dataset_config()

active_role = os.getenv("ACTIVE_USER_ROLE", "viewer")

# Initialize the agent with the dynamic role
root_agent = get_root_agent(user_role=active_role)

























# """Top level agent for data agent multi-agents."""

# import json
# import logging
# import os
# import importlib.resources

# from google.adk.agents import LlmAgent
# from google.genai import types

# from .prompts import return_instructions_root


# from .tools import call_hr_agent, call_sales_agent, call_reporting_agent

# logging.basicConfig(level=logging.INFO)
# _logger = logging.getLogger(__name__)

# _dataset_config = {}

# def load_dataset_config():
#     """Load the dataset configurations for the agent from the config file"""
#     dataset_config_file = os.getenv("DATASET_CONFIG_FILE", "master_config.json")
#     filename_only = os.path.basename(dataset_config_file)
#     dataset_config = None
    
#     try:
#         config_text = importlib.resources.read_text("data_science", filename_only)
#         dataset_config = json.loads(config_text)
#     except Exception:
#         pass
        
#     if dataset_config is None:
#         possible_paths = [dataset_config_file, f"data_science/{filename_only}", f"./{filename_only}"]
#         for path in possible_paths:
#             if os.path.exists(path):
#                 with open(path, "r", encoding="utf-8") as f:
#                     dataset_config = json.load(f)
#                 break

#     if dataset_config is None:
#         raise FileNotFoundError(f"CRITICAL: Could not find dataset config file: {dataset_config_file}")

#     return dataset_config

# def get_dataset_definitions_for_instructions() -> str:
#     """Returns the dataset definitions instructions block WITHOUT heavy schemas"""
#     dataset_definitions = "\n<DATASETS>\n"
    
#     for dataset in _dataset_config["datasets"]:
#         dataset_name = dataset["name"]
        
#         dataset_definitions += f"""
# <{dataset_name.upper()}>
# <DESCRIPTION>
# {dataset["description"]}
# </DESCRIPTION>
# </{dataset_name.upper()}>
# """
        
#     dataset_definitions += "</DATASETS>\n"
#     return dataset_definitions

# def get_root_agent() -> LlmAgent:
#     tools = []
    
#     for dataset in _dataset_config["datasets"]:
#         if dataset["name"] == "people_analytics":
#             tools.append(call_hr_agent)
#         elif dataset["name"] == "sales_and_customers":
#             tools.append(call_sales_agent)

#     agent = LlmAgent(
#         model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-pro"),
#         name="data_science_root_agent",
#         instruction=return_instructions_root() + get_dataset_definitions_for_instructions(),
#         tools=tools + [call_reporting_agent], 
#         generate_content_config=types.GenerateContentConfig(temperature=0.01),
#     )
#     return agent

# _dataset_config = load_dataset_config()
# root_agent = get_root_agent()



















