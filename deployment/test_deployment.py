import asyncio
import os
import sys

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from google.adk.sessions import VertexAiSessionService
from vertexai import agent_engines

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket (without gs:// prefix).")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")
flags.DEFINE_string("user_id", None, "User ID (can be any string).")

flags.mark_flag_as_required("resource_id")
flags.mark_flag_as_required("user_id")

def main(argv: list[str]) -> None:
    load_dotenv()

    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location or os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = FLAGS.bucket or os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    if not project_id or not location or not bucket:
        print("Error: Missing required GCP configurations.")
        return

    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket}")
    session_service = VertexAiSessionService(project_id, location)
    
    print("Creating session...")
    session = asyncio.run(session_service.create_session(app_name=FLAGS.resource_id, user_id=FLAGS.user_id))
    
    # Handle both object and dictionary return types for session
    session_id = session.id if hasattr(session, 'id') else session.get('id')
    print(f"Created session for user ID: {FLAGS.user_id} (Session ID: {session_id})")

    try:
        agent = agent_engines.get(FLAGS.resource_id)
        print(f"Connected to Cloud Agent: {FLAGS.resource_id}")

        while True:
            user_input = input("\nInput: ")
            if user_input.strip().lower() in ["quit", "exit"]:
                break

            print("Response: ", end="")
            for event in agent.stream_query(user_id=FLAGS.user_id, session_id=session_id, message=user_input):
                if "content" in event and "parts" in event["content"]:
                    for part in event["content"]["parts"]:
                        if "text" in part:
                            sys.stdout.write(part["text"])
                            sys.stdout.flush()
            print()

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("Cleaning up session...")
        asyncio.run(session_service.delete_session(app_name=FLAGS.resource_id, user_id=FLAGS.user_id, session_id=session_id))
        print("Done.")

if __name__ == "__main__":
    app.run(main)