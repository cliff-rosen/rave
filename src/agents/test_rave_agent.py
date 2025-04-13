from rave_agent import (
    graph,
    Scorecard,
    SearchHistory,
    AttemptHistory,
    State
)

def main2():

    initial_state: State = {
        "messages": [],
        "query": "What are the key differences between supervised and unsupervised learning in machine learning?",
        "scorecard": Scorecard(
            completeness=0.0,
            accuracy=0.0,
            relevance=0.0,
            clarity=0.0
        ),
        "search_history": SearchHistory(queries=[], results=[]),
        "attempt_history": AttemptHistory(responses=[], scores=[], feedback=[]),
        "current_gaps": [],
        "current_attempt": """Supervised and unsupervised learning are ...""",
        "new_queries": [],
        "search_results": []
    }


    # Run the graph
    print("Starting RAVE agent...")
    
    try:
        # The graph will automatically handle the refinement process
        result = graph.stream(initial_state, stream_mode="custom")

        # Print final results
        print("\nFinal Results:")
        print("=" * 50)
        print(f"Final Response: {result['current_attempt']}")
        print("\nScorecard History:")
        for i, score in enumerate(result['attempt_history'].scores):
            print(f"Attempt {i+1}:")
            print(f"  Completeness: {score.completeness:.2f}")
            print(f"  Accuracy: {score.accuracy:.2f}")
            print(f"  Relevance: {score.relevance:.2f}")
            print(f"  Clarity: {score.clarity:.2f}")
        
        print("\nSearch History:")
        for i, query in enumerate(result['search_history'].queries):
            print(f"Query {i+1}: {query}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    initial_state: State = {
        "x": "hello",
        "y": "world"
    }
    
    print("Starting agent...")
    
    try:
        # Stream with custom mode to get incremental updates
        for chunk in graph.stream(initial_state, stream_mode="custom"):
            print("Custom stream data:", chunk)
            # Here you would handle each piece of data from the StreamWriter
            # For example, updating a progress bar, displaying intermediate results, etc.
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    main() 