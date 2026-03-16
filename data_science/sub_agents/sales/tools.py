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

"""This file contains the tools used by the database agent."""

import logging
import os
import re

from google.adk.tools import ToolContext
from google.adk.tools.bigquery.client import get_bigquery_client
from google.genai import Client
from google.genai.types import HttpOptions

from data_science.utils.utils import USER_AGENT, get_env_var

logger = logging.getLogger(__name__)

# Core Environment Variables
data_project = get_env_var("BQ_DATA_PROJECT_ID")
compute_project = get_env_var("BQ_COMPUTE_PROJECT_ID")
vertex_project = get_env_var("GOOGLE_CLOUD_PROJECT")
location = get_env_var("GOOGLE_CLOUD_LOCATION")
http_options = HttpOptions(headers={"user-agent": USER_AGENT})

llm_client = Client(
    vertexai=True,
    project=vertex_project,
    location=location,
    http_options=http_options,
)

MAX_NUM_ROWS = 10000

def get_filtered_schema(target_dataset_id: str, question: str = ""):
    """Retrieves schema dynamically and filters based on the natural language question."""
    client = get_bigquery_client(
        project=compute_project,
        credentials=None,
        user_agent=USER_AGENT,
    )
    
    query = f"""
        SELECT table_name, column_name, data_type, description
        FROM `{data_project}.{target_dataset_id}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
    """
    df_schema = client.query(query).to_dataframe()
    df_schema['description'] = df_schema['description'].fillna('')
    
    if len(df_schema) > 30 and question:
        keywords = [re.escape(kw) for kw in question.lower().split()]
        pattern = '|'.join(keywords)
        
        relevant_df = df_schema[
            df_schema['column_name'].str.contains(pattern, case=False, na=False) |
            df_schema['description'].str.contains(pattern, case=False, na=False)
        ]
        
        df_schema = relevant_df if not relevant_df.empty else df_schema.head(20)

    tables_context = {}
    for table in df_schema['table_name'].unique():
        table_rows = df_schema[df_schema['table_name'] == table]
        schema_list = [
            f"{row['column_name']} ({row['data_type']}) - Desc: {row['description'] or 'N/A'}"
            for _, row in table_rows.iterrows()
        ]
        tables_context[f"{data_project}.{target_dataset_id}.{table}"] = {
            "table_schema": schema_list
        }

    return tables_context

def sales_nl2sql(question: str, tool_context: ToolContext) -> str:
    """Generates a SQL query from a natural language question."""
    logger.debug("sales_nl2sql - question: %s", question)
    
    sales_dataset_id = "sales_and_customers" 
    
    # DYNAMIC FETCH: Pull schema specifically tailored to this question
    dynamic_schema = get_filtered_schema(sales_dataset_id, question)

    prompt_template = """
You are a BigQuery SQL expert tasked with generating SQL in the Google SQL dialect.

**Guidelines:**
- **Table Referencing:** Always use the full table name: `project_name.dataset_name.table_name`.
- **SQL Syntax:** Return syntactically and semantically correct SQL.
- **Column Usage:** Use ONLY the column names mentioned below.
- **LIMIT ROWS:** Max rows < {MAX_NUM_ROWS}.

**Relevant Schema:**
{SCHEMA}

**Natural language question:**
{QUESTION}

Only output the SQL query.
""" 

    prompt = prompt_template.format(
        MAX_NUM_ROWS=MAX_NUM_ROWS, SCHEMA=dynamic_schema, QUESTION=question
    )

    try:
        response = llm_client.models.generate_content(
            model=os.getenv("SALES_AGENT_MODEL", "gemini-2.5-pro"),
            contents=prompt,
            config={"temperature": 0.1},
        )
        sql = (response.text or "").replace("```sql", "").replace("```", "").strip()
    except Exception as e:
        logger.error(f"LLM Generation failed: {e}")
        return f"Error generating SQL: {str(e)}"

    if not sql:
        return "No SQL query was generated. Please rephrase your question."

    # --- SECURITY GUARDRAIL ---
    if re.search(r"(?i)\b(update|delete|drop|insert|create|alter|truncate|merge|grant|revoke)\b", sql):
        logger.warning(f"Blocked malicious SQL execution attempt: {sql}")
        tool_context.state["sql_query"] = "INVALID_SQL"
        return "SECURITY ALERT: Only SELECT queries are permitted."

    tool_context.state["sql_query"] = sql
    return sql



























































































# """This file contains the tools used by the database agent."""

# import datetime
# import logging
# import os
# import re
# import numpy as np
# import pandas as pd

# from google.adk.tools import ToolContext
# from google.adk.tools.bigquery.client import get_bigquery_client
# from google.cloud import bigquery
# from google.genai import Client
# from google.genai.types import HttpOptions

# from data_science.utils.utils import USER_AGENT, get_env_var

# logger = logging.getLogger(__name__)

# # Core Environment Variables
# data_project = get_env_var("BQ_DATA_PROJECT_ID")
# compute_project = get_env_var("BQ_COMPUTE_PROJECT_ID")
# vertex_project = get_env_var("GOOGLE_CLOUD_PROJECT")
# location = get_env_var("GOOGLE_CLOUD_LOCATION")
# http_options = HttpOptions(headers={"user-agent": USER_AGENT})

# llm_client = Client(
#     vertexai=True,
#     project=vertex_project,
#     location=location,
#     http_options=http_options,
# )

# MAX_NUM_ROWS = 10000
# database_settings = None


# def _serialize_value_for_sql(value):
#     """Serializes a Python value from a pandas DataFrame into a BigQuery SQL literal."""
#     if isinstance(value, (list, np.ndarray)):
#         return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
#     if pd.isna(value):
#         return "NULL"
#     if isinstance(value, str):
#         new_value = value.replace("\\", "\\\\").replace("'", "''")
#         return f"'{new_value}'"
#     if isinstance(value, bytes):
#         decoded = value.decode("utf-8", "replace")
#         new_value = decoded.replace("\\", "\\\\").replace("'", "''")
#         return f"b'{new_value}'"
#     if isinstance(value, (datetime.datetime, datetime.date, pd.Timestamp)):
#         return f"'{value}'"
#     if isinstance(value, dict):
#         string_values = [_serialize_value_for_sql(v) for v in value.values()]
#         return f"({', '.join(string_values)})"
#     return str(value)


# def get_specific_bigquery_schema(target_dataset_id: str):
#     """Retrieves schema and sample values for a specific BigQuery dataset."""
#     client = get_bigquery_client(
#         project=compute_project,
#         credentials=None,
#         user_agent=USER_AGENT,
#     )
#     dataset_ref = bigquery.DatasetReference(data_project, target_dataset_id)
#     tables_context = {}
    
#     for table in client.list_tables(dataset_ref):
#         table_info = client.get_table(
#             bigquery.TableReference(dataset_ref, table.table_id)
#         )
#         table_schema = [
#             (schema_field.name, schema_field.field_type)
#             for schema_field in table_info.schema
#         ]
#         table_ref = dataset_ref.table(table.table_id)
#         sample_values = []
        
#         # Adjust sampling logic as needed
#         if False:
#             sample_query = f"SELECT * FROM `{table_ref}` LIMIT 5"
#             sample_values = (
#                 client.query(sample_query).to_dataframe().to_dict(orient="list")
#             )
#             for key in sample_values:
#                 sample_values[key] = [
#                     _serialize_value_for_sql(v) for v in sample_values[key]
#                 ]
#         tables_context[str(table_ref)] = {
#             "table_schema": table_schema,
#             "example_values": sample_values,
#         }

#     return tables_context


# def update_database_settings():
#     # Hardcode the Sales dataset ID
#     sales_dataset_id = "sales_and_customers" 
#     schema = get_specific_bigquery_schema(sales_dataset_id)
    
#     return {
#         "dataset_id": sales_dataset_id,
#         "schema": schema,
#     }


# def get_database_settings():
#     """Get database settings."""
#     global database_settings
#     if database_settings is None:
#         database_settings = update_database_settings()
#     return database_settings


# def sales_nl2sql(
#     question: str,
#     tool_context: ToolContext,
# ) -> str:
#     """Generates a SQL query from a natural language question."""
#     logger.debug("sales_nl2sql - question: %s", question)
#     sql = "" 

#     prompt_template =  """
# You are a BigQuery SQL expert tasked with generating SQL in the Google SQL
# dialect based on the user's natural language question.
# Your task is to write a Bigquery SQL query that answers the following question
# while using the provided context.

# **Guidelines:**
# - **Table Referencing:** Always use the full table name with the database prefix: `project_name.dataset_name.table_name`.
# - **Joins:** Join as few tables as possible. 
# - **Aggregations:** Use all non-aggregated columns from the `SELECT` statement in the `GROUP BY` clause.
# - **SQL Syntax:** Return syntactically and semantically correct SQL for BigQuery.
# - **Column Usage:** Use *ONLY* the column names mentioned in the Table Schema.
# - **LIMIT ROWS:** The maximum number of rows returned should be less than {MAX_NUM_ROWS}.

# **Schema:**
# {SCHEMA}


# **Natural language question:**
# {QUESTION}


# **Think Step-by-Step:** Carefully consider the schema, question, guidelines, and
# best practices outlined above to generate the correct BigQuery SQL. Only output the SQL query.
# """ 


#     schema = tool_context.state["sales_database_settings"]["schema"]

#     prompt = prompt_template.format(
#         MAX_NUM_ROWS=MAX_NUM_ROWS, SCHEMA=schema, QUESTION=question
#     )

#     try:
#         response = llm_client.models.generate_content(
#             model=os.getenv("SALES_AGENTMODEL", "gemini-2.5-pro"),
#             contents=prompt,
#             config={"temperature": 0.1},
#         )
#         generated_text = response.text if response.text else ""
#         sql = generated_text.replace("```sql", "").replace("```", "").strip()
#     except Exception as e:
#         logger.error(f"LLM Generation failed: {e}")
#         return f"Error generating SQL: {str(e)}"

#     if not sql:
#         return "No SQL query was generated. Please rephrase your question."

#     # --- SECURITY GUARDRAIL: REGEX CHECK ---
#     malicious_patterns = r"(?i)\b(update|delete|drop|insert|create|alter|truncate|merge|grant|revoke)\b"
    
#     if re.search(malicious_patterns, sql):
#         logger.warning(f"Blocked malicious SQL execution attempt: {sql}")
#         error_msg = "SECURITY ALERT: Only SELECT queries are permitted."
#         tool_context.state["sql_query"] = "INVALID_SQL"
#         return error_msg
#     # ---------------------------------------

#     logger.debug("sales_nl2sql - sql:\n%s", sql)
#     tool_context.state["sql_query"] = sql

#     return sql