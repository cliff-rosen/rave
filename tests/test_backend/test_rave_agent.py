import pytest
from backend.agents.rave_agent import (
    State,
    Scorecard,
    SearchHistory,
    AttemptHistory,
    graph
)

def test_initial_state():
    """Test that the initial state is properly structured"""
    initial_state = {
        "messages": [],
        "query": "Test query",
        "scorecard": None,
        "search_history": SearchHistory(queries=[], results=[]),
        "attempt_history": AttemptHistory(responses=[], scores=[], feedback=[]),
        "current_gaps": [],
        "current_attempt": None,
        "new_queries": [],
        "search_results": []
    }
    
    assert isinstance(initial_state, dict)
    assert initial_state["query"] == "Test query"
    assert isinstance(initial_state["search_history"], SearchHistory)
    assert isinstance(initial_state["attempt_history"], AttemptHistory)

def test_scorecard_validation():
    """Test that scorecard values are properly validated"""
    valid_scorecard = Scorecard(
        completeness=0.8,
        accuracy=0.9,
        relevance=0.85,
        clarity=0.75
    )
    
    assert valid_scorecard.completeness == 0.8
    assert valid_scorecard.accuracy == 0.9
    assert valid_scorecard.relevance == 0.85
    assert valid_scorecard.clarity == 0.75
    
    # Test invalid values
    with pytest.raises(ValueError):
        Scorecard(
            completeness=1.5,  # Invalid: > 1.0
            accuracy=0.9,
            relevance=0.85,
            clarity=0.75
        )

def test_graph_structure():
    """Test that the graph has the expected structure"""
    nodes = graph.nodes
    edges = graph.edges
    
    # Check for required nodes
    required_nodes = {
        "evaluator",
        "gap_analyzer",
        "query_generator",
        "search",
        "response_generator"
    }
    assert all(node in nodes for node in required_nodes)
    
    # Check for required edges
    required_edges = {
        ("evaluator", "gap_analyzer"),
        ("gap_analyzer", "query_generator"),
        ("query_generator", "search"),
        ("search", "response_generator"),
        ("response_generator", "evaluator")
    }
    assert all(edge in edges for edge in required_edges)

def test_state_transitions():
    """Test that state transitions work as expected"""
    initial_state = {
        "messages": [],
        "query": "What is machine learning?",
        "scorecard": None,
        "search_history": SearchHistory(queries=[], results=[]),
        "attempt_history": AttemptHistory(responses=[], scores=[], feedback=[]),
        "current_gaps": [],
        "current_attempt": "Machine learning is a subset of AI.",
        "new_queries": [],
        "search_results": []
    }
    
    # Test that the graph can process the initial state
    try:
        for output in graph.stream(initial_state):
            assert isinstance(output, tuple)
            output_type, output_data = output
            assert output_type in ["updates", "final"]
    except Exception as e:
        pytest.fail(f"Graph processing failed: {str(e)}") 