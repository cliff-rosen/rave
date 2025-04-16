import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from backend.agents.rave_agent import (
    graph,
    State
)

def main():
    initial_state: State = {
        "messages": [],
        "question": "What is the capital of France?",
        "answer": "",
        "improved_question": None,
        "scored_checklist": [],
        "knowledge_base": []
    }
    
    print("Starting agent...")
    
    try:
        for chunk in graph.stream(initial_state, stream_mode=["values", "custom"]):
            print("Stream data:", chunk)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    main() 