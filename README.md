Here is your polished and formatted `README.md` file. You can copy this directly into your project's `README.md` file.

---

# Custom-Agent: Multi-Agent Data Orchestrator

`custom-agent` is a modular, multi-agent system powered by LLMs, designed to bridge the gap between natural language queries and structured data operations. It orchestrates specialized sub-agents to perform NL2SQL tasks, data synthesis, and Slack reporting within a Google Cloud Platform environment.

## 🚀 Key Features

- **Hub-and-Spoke Architecture**: A central "Root Agent" delegates tasks to domain-specific sub-agents (HR, Sales, Reporting).
- **Dynamic Schema Retrieval**: Automatically filters and fetches BigQuery schema relevant to the user query, reducing token cost and resolving ambiguous column names via `INFORMATION_SCHEMA`.
- **Self-Correction Loops**: Agents are instructed to identify syntax errors from database logs and re-attempt queries automatically.
- **Security Guardrails**: Built-in Regex filters prevent malicious DML/DDL commands (DROP, DELETE, etc.) from being executed.
- **Cloud-Native**: Fully optimized for deployment on Vertex AI Agent Engine and registration within Gemini Enterprise.

## 🏗️ Project Structure

```text
custom-agent/
├── data_science/           # Core Agent logic
│   ├── sub_agents/         # Domain-specific logic (HR, Sales, Slack)
│   │   ├── hr/             # Employee & Skills specialist
│   │   ├── sales/          # Revenue & Profit specialist
│   │   └── slack_report/   # Communications specialist
│   ├── agent.py            # Root orchestrator definition
│   ├── master_config.json  # Global dataset & routing mapping
│   └── tools.py            # Orchestrator-level tools
├── deployment/             # Vertex AI deployment scripts & built wheels
├── tests/                  # Pytest suite for agent validation
├── main.py                 # FastAPI server for Cloud Run deployment
└── pyproject.toml          # Project dependencies and build config
```

## 🛠️ Prerequisites

- **Python 3.12+**
- **uv** (for lightning-fast dependency and virtualenv management)
- **Google Cloud SDK** (authenticated with project permissions)
- **Slack Webhook URL** (required for the reporting sub-agent)

## 🚀 Getting Started

### 1. Installation

Clone the repository and use `uv` to synchronize the environment:

```bash
git clone https://github.com/your-username/custom-agent.git
cd custom-agent
uv sync
```

### 2. Configuration

Copy the template environment file and populate it with your GCP details:

```bash
cp toolbox.env-example .env
# Edit .env with your Project ID, Location, and Slack Webhook
```

### 3. Dataset Configuration

Define your BigQuery tables in `data_science/master_config.json`. This file acts as the map for the Root Agent to understand which sub-agent handles which data domain.

### 4. Local Testing

Run the agent locally to verify connections and logic before deploying to the cloud.

**CLI Mode (Interactive Terminal):**

```bash
uv run adk run data_science
```

**Web UI Mode (Local Browser Interface):**

```bash
uv run adk web data_science
```

## 🧪 Testing

Run the integrated test suite to verify agent orchestration and database connectivity:

```bash
uv run pytest tests/
```

## ☁️ Deployment on Vertex AI Agent Engine

### 1. Initial Setup

To deploy the agent to Google Agent Engine, you must first configure IAM permissions for the Reasoning Engine Service Agent. Replace `${GOOGLE_CLOUD_PROJECT_NUMBER}` and `${GOOGLE_CLOUD_PROJECT}` with your specific project details:

```bash
export RE_SA="service-${GOOGLE_CLOUD_PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

# Grant BigQuery and Vertex AI permissions
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${RE_SA}" \
    --role="roles/bigquery.user"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${RE_SA}" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${RE_SA}" \
    --role="roles/aiplatform.user"
```

### 2. Agent Deployment

Build your agent into a Python wheel and use the deployment script to push it to Vertex AI:

```bash
# Generate the .whl file
uv build --wheel --out-dir deployment

# Deploy to Vertex AI
cd deployment/
python deploy.py --create
```

Upon success, the script will output a **Resource Name** (e.g., `projects/.../locations/us-central1/reasoningEngines/12345`). Copy this ID; you will need it for the next step.

## 💎 Agent Registration in Gemini Enterprise

After deploying to the Agent Engine, you must register the agent within Gemini Enterprise to make it available to your organization:

1.  **Open Gemini Enterprise**: Navigate to your created App.
2.  **Add Agent**: Click on **Agents** in the sidebar and select **Add Agent**.
3.  **Source Selection**: Choose **Add from Custom agent via Agent Engine**.
4.  **Connect**: Click **Next** and paste the **Resource Name** you copied from the deployment step into the _Reasoning Engine_ field.
5.  **Finalize**: Complete the agent details. The agent will now appear in your list and can be used directly within the Gemini Enterprise interface.

## 🛡️ Security & Observability

- **Security**: Hardcoded Regex filters inside `hr_nl2sql` and `sales_nl2sql` tools block any non-SELECT queries (DROP, DELETE, UPDATE), ensuring the system remains strictly read-only.
- **Observability**: Fully instrumented with **OpenTelemetry**. Traces are exported to GCP Cloud Trace, allowing you to monitor latency and view waterfall charts of agent-to-agent communication.

---

_Built with the Google ADK (Agent Development Kit)_
