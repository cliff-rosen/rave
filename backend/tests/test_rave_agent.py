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
    initial_state = {
        "messages": [],
        "question": "What is business?",
        "improved_question": None,
        "current_query": None,
        "query_history": [],
        "search_results": [],
        "scored_checklist": [],
        "answer": None,
        "knowledge_base": []
    }

    config = {
        "configurable": {
            "question_model": "gpt-4o-mini",
            "checklist_model": "gpt-4o-mini",
            "query_model": "gpt-4o-mini",
            "answer_model": "gpt-4o-mini",
            "scoring_model": "gpt-4o-mini",
            "kb_model": "gpt-4o-mini",
            "max_iterations": 2,
            "score_threshold": 0.5
        }
    }


    print("Starting agent...")
    
    try:
        for chunk in graph.stream(initial_state, config=config, stream_mode=["values", "custom"]):
            print("Stream data:", chunk)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    main() 