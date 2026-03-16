# Copyright 2025 Google LLC
# [License omitted for brevity]

"""Test deployment of Data Science Agent to Agent Engine."""

import asyncio
import os
import sys

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from google.adk.sessions import VertexAiSessionService
from vertexai import agent_engineswh

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket (without gs:// prefix).")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")
flags.DEFINE_string("user_id", None, "User ID (can be any string).")

flags.mark_flag_as_required("resource_id")
flags.mark_flag_as_required("user_id")


def main(argv: list[str]) -> None:  # pylint: disable=unused-argument
    load_dotenv()

    # Use FLAGS if provided, otherwise fallback to .env variables
    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location or os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = FLAGS.bucket or os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    # Validation
    if not project_id:
        print("Error: Missing required environment variable or flag: GOOGLE_CLOUD_PROJECT / --project_id")
        return
    if not location:
        print("Error: Missing required environment variable or flag: GOOGLE_CLOUD_LOCATION / --location")
        return
    if not bucket:
        print("Error: Missing required environment variable or flag: GOOGLE_CLOUD_STORAGE_BUCKET / --bucket")
        return

    # Initialize SDKs
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    session_service = VertexAiSessionService(project_id, location)
    
    print("Creating session...")
    session = asyncio.run(
        session_service.create_session(
            app_name=FLAGS.resource_id, user_id=FLAGS.user_id
        )
    )
    print(f"Created session for user ID: {FLAGS.user_id} (Session ID: {session.id})")

    try:
        agent = agent_engines.get(FLAGS.resource_id)
        print(f"Found agent with resource ID: {FLAGS.resource_id}")

        print("\nType 'quit' to exit.")
        while True:
            user_input = input("\nInput: ")
            if user_input.strip().lower() == "quit":
                break

            print("Response: ", end="")
            
            # Stream the response naturally to the console
            for event in agent.stream_query(
                user_id=FLAGS.user_id, session_id=session.id, message=user_input
            ):
                if "content" in event and "parts" in event["content"]:
                    for part in event["content"]["parts"]:
                        if "text" in part:
                            sys.stdout.write(part["text"])
                            sys.stdout.flush()
                            
            print()  # Add a newline when the stream finishes

    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        
    finally:
        # Guarantee cleanup even if an error occurs or the user interrupts the script
        print("\nCleaning up...")
        asyncio.run(
            session_service.delete_session(
                app_name=FLAGS.resource_id,
                user_id=FLAGS.user_id,
                session_id=session.id,
            )
        )
        print(f"Deleted session for user ID: {FLAGS.user_id}")


if __name__ == "__main__":
    app.run(main)