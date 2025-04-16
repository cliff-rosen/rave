import streamlit as st
from backend.agents.rave_agent import graph

# Clear all state if not done already
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.initialized = True

st.title("RAVE Agent Interface")

# Initialize session state for input if not exists
if "query" not in st.session_state:
    st.session_state.query = ""

# Add restart button
if st.button("Restart"):
    st.session_state.query = ""
    st.rerun()

# Get text input from user
user_input = st.text_input("Enter your query:", key="query")

if user_input:
    # Initialize state with the user's input
    initial_state = {"x": user_input, "y": []}
    
    # Create two columns
    left_col, right_col = st.columns(2)
    
    # Initialize step messages
    step_messages = {}
    
    # Run the graph with streaming
    for output in graph.stream(initial_state, stream_mode=["updates", "custom"]):
        output_type, output_data = output

        if output_type == "custom":
            msg = output_data["msg"]
            if isinstance(msg, dict) and "step" in msg:
                if msg["step"] not in step_messages:
                    step_messages[msg["step"]] = []
                step_messages[msg["step"]].append(msg["count"])
                
                # Display messages in left column
                with left_col:
                    st.write(f"Step {msg['step']}: {msg['count']}")
                
                # Display values in right column
                with right_col:
                    st.write(f"Step {msg['step']} values: {msg['count']}")
