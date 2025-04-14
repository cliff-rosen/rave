import streamlit as st
from backend.agents.rave_agent import graph
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RAVE - Recursive Agent for Verified Explanations",
    page_icon="🤖",
    layout="wide"
)

# Styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 1.2rem;
    }
    .status-message {
        color: #666;
        font-style: italic;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .status-area {
        height: 300px;
        overflow-y: auto;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.initialized = True
    st.session_state.current_question = ""
    st.session_state.status_messages = []
    st.session_state.current_values = {}

# Header
st.title("🤖 RAVE - Recursive Agent")
st.subheader("Your AI Assistant for Verified Explanations")

# Sidebar
with st.sidebar:
    st.header("Status")
    st.markdown("---")
    
    # New Conversation button
    if st.button("New Conversation", type="primary"):
        st.session_state.current_question = ""
        st.session_state.status_messages = []
        st.session_state.current_values = {}
        st.rerun()
    
    # Fixed height status area
    st.markdown('<div class="status-area">', unsafe_allow_html=True)
    for msg in st.session_state.status_messages:
        st.markdown(f'<div class="status-message">{msg}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Main interface
question = st.text_input(
    "What would you like to know?",
    key="current_question",
    placeholder="Enter your question here..."
)

if question and question != st.session_state.get("last_question", ""):
    st.session_state.last_question = question
    
    # Initialize display areas
    st.markdown("### Output Values")
    values_placeholder = st.empty()
    
    # Initialize state for the agent
    initial_state = {
        "messages": [],
        "question": question,
        "answer": None
    }
    
    # Process with the agent
    try:
        for output in graph.stream(initial_state, stream_mode=["values", "custom"]):
            print(output)
            
            # Handle different types of output
            if isinstance(output, tuple):
                output_type, output_data = output
                
                if output_type == "custom":
                    # Add new status message
                    new_message = output_data.get("msg", "")
                    if new_message:
                        st.session_state.status_messages.append(new_message)
                        # Rerun to update the status area
                        st.rerun()
                
                elif output_type == "values":
                    # Update values
                    st.session_state.current_values = output_data
                    with values_placeholder:
                        st.json(st.session_state.current_values)
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}") 