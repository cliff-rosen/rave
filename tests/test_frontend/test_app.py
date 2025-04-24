import pytest
from streamlit.testing.v1 import AppTest
from frontend.app_bak import st

def test_app_initialization():
    """Test that the app initializes correctly"""
    at = AppTest.from_file("frontend/app.py")
    at.run()
    
    # Check that the title is present
    assert "RAVE - Recursive Agent" in at.get("title")
    
    # Check that the input field is present
    assert at.text_input("What would you like to know?") is not None
    
    # Check that the sidebar is present
    assert "Settings" in at.sidebar.get("header")

def test_session_state():
    """Test that session state is properly initialized"""
    at = AppTest.from_file("frontend/app.py")
    at.run()
    
    # Check initial session state
    assert "initialized" in at.session_state
    assert "history" in at.session_state
    assert "current_query" in at.session_state
    assert "current_response" in at.session_state

def test_query_processing():
    """Test that queries are processed correctly"""
    at = AppTest.from_file("frontend/app.py")
    at.run()
    
    # Enter a test query
    at.text_input("What would you like to know?").input("What is AI?")
    
    # Check that the query is processed
    assert at.session_state["current_query"] == "What is AI?"
    
    # Check that the response area is updated
    assert at.empty() is not None  # Response placeholder

def test_history_tracking():
    """Test that conversation history is properly tracked"""
    at = AppTest.from_file("frontend/app.py")
    at.run()
    
    # Enter multiple queries
    queries = ["What is AI?", "How does it work?", "What are its applications?"]
    for query in queries:
        at.text_input("What would you like to know?").input(query)
        at.run()
    
    # Check that history is properly maintained
    assert len(at.session_state["history"]) == len(queries)
    
    # Check that each history item has the required fields
    for item in at.session_state["history"]:
        assert "query" in item
        assert "response" in item
        assert "scorecard" in item

def test_reset_functionality():
    """Test that the reset button works correctly"""
    at = AppTest.from_file("frontend/app.py")
    at.run()
    
    # Add some history
    at.text_input("What would you like to know?").input("Test query")
    at.run()
    
    # Click the reset button
    at.sidebar.button("New Conversation").click()
    at.run()
    
    # Check that history is cleared
    assert len(at.session_state["history"]) == 0
    assert at.session_state["current_query"] == ""
    assert at.session_state["current_response"] == "" 