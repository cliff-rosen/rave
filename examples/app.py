import streamlit as st
from src.agents.rave_agent import graph

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
    
    # Create containers for each step
    step_containers = {}
    
    # Initialize step messages
    step_messages = {}
    
    # Create a placeholder for all output
    output_area = st.empty()
    
    # Run the graph with streaming
    for output in graph.stream(initial_state, stream_mode=["updates", "custom"]):
        print(output)
        output_type, output_data = output

        if output_type == "custom":
            msg = output_data["msg"]
            if isinstance(msg, dict) and "step" in msg:
                if msg["step"] not in step_messages:
                    step_messages[msg["step"]] = []
                step_messages[msg["step"]].append(msg["count"])
                
                # Build the complete output text
                output_text = ""
                for step in sorted(step_messages.keys()):
                    output_text += f"Step {step}:\n"
                    output_text += ",".join(map(str, step_messages[step]))
                    output_text += "\n\n"
                
                # Update the display
                output_area.text(output_text)
