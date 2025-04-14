from backend.agents.rave_agent import (
    graph,
    State
)

def main():
    initial_state: State = {
        "x": "hello",
        "y": "world"
    }
    
    print("Starting agent...")
    
    try:
        for chunk in graph.stream(initial_state, stream_mode="custom"):
            print("Custom stream data:", chunk)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    main() 