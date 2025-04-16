import sys
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Debug: Print current working directory and .env path
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
env_path = find_dotenv()
print(f".env file path: {env_path}")

# Debug: Print contents of .env file if it exists
if env_path and os.path.exists(env_path):
    print("\nContents of .env file:")
    with open(env_path, 'r') as f:
        print(f.read())

# Check for environment variable before loading .env
print("\nEnvironment variable before loading .env:")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
if 'OPENAI_API_KEY' in os.environ:
    print(f"OPENAI_API_KEY value: {os.environ['OPENAI_API_KEY']}")

# Load environment variables
if not env_path:
    raise FileNotFoundError("Could not find .env file. Please create one in the project root directory.")

# Clear the environment variable before loading .env
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

load_dotenv(env_path, override=True)

# Debug: Print environment variables after loading
print("\nEnvironment variables after loading .env:")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
print(f"OPENAI_API_KEY length: {len(os.getenv('OPENAI_API_KEY', ''))} characters")
print(f"OPENAI_API_KEY starts with: {os.getenv('OPENAI_API_KEY', '')[:7]}...")
print(f"OPENAI_API_KEY full value: {os.getenv('OPENAI_API_KEY', '')}")

# Verify OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")

from src.agents.conversational_agent import graph
from langchain_core.messages import HumanMessage, AIMessageChunk
import asyncio

async def stream_graph_updates(user_input: str):
    # Create a properly formatted message
    message = HumanMessage(content=user_input)
    print("Assistant: ", end="", flush=True)
    
    try:
        last_content = ""
        async for event in graph.astream({"messages": [message]}):
            # When using stream_mode="messages", event is a tuple of (message_chunk, metadata)
            if isinstance(event, tuple):
                message_chunk, metadata = event
                if isinstance(message_chunk, AIMessageChunk):
                    # Print the new content
                    print(message_chunk.content, end="", flush=True)
            else:
                # Handle other event formats if needed
                for value in event.values():
                    if value["messages"]:
                        current_content = value["messages"][-1].content
                        # Only print the new content
                        if len(current_content) > len(last_content):
                            print(current_content[len(last_content):], end="", flush=True)
                            last_content = current_content
        print()  # New line after response is complete
    except Exception as e:
        print(f"\nError in stream_graph_updates: {e}")
        raise

def run_graph(user_input: str):
    config = {"configurable": {"thread_id": "1"}}
    message = HumanMessage(content=user_input)
    print("Assistant: ", end="", flush=True)
    res = graph.invoke({"messages": [message]}, config)
    print(res["messages"][-1].content)

def main():
    print("Starting conversation...")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            run_graph(user_input)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()

