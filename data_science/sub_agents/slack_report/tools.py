"""Tools for the Reporting Agent."""

import os
import requests
import logging
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

def send_slack_message(
    message: str,
    tool_context: ToolContext,
) -> str:
    """Sends a formatted message to a Slack channel using a Webhook."""
    logger.debug("Sending message to Slack...")
    
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return "ERROR: SLACK_WEBHOOK_URL environment variable is not set."
    
    # Slack expects a JSON payload with a "text" key
    payload = {"text": message}
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            return "SUCCESS: Message sent to Slack."
        else:
            return f"FAILED: Slack API returned status {response.status_code}, {response.text}"
    except Exception as e:
        logger.error(f"Failed to send Slack message: {e}")
        return f"ERROR: Exception occurred while sending to Slack: {str(e)}"