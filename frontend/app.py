import streamlit as st
from backend.agents.rave_agent import graph
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RAVE - Recursive Agent for Verified Explanations",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Apply dark theme and custom styling
st.markdown("""
    <style>
    /* Dark theme */
    :root {
        --background-color: #1e1e2e;
        --text-color: #ffffff;
        --sidebar-color: #2b2b3a;
        --status-bg-color: #2b2b3a;
    }
    
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
        padding: 1rem;
    }
    
    header {
        background-color: var(--background-color);
        visibility: hidden;
    }
    
    .sidebar .sidebar-content {
        background-color: var(--sidebar-color);
        color: var(--text-color);
    }
    
    /* Status area styling */
    .status-message {
        color: #cccccc;
        font-style: italic;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    
    .status-area {
        height: 200px;
        overflow-y: auto;
        padding: 0.5rem;
        background-color: var(--status-bg-color);
        border-radius: 0.25rem;
        margin-top: 0.5rem;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        font-size: 1.2rem;
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    /* JSON output styling */
    .element-container div[data-testid="stJson"] {
        background-color: #2b2b3a;
        border-radius: 0.25rem;
        padding: 1rem;
    }
    
    /* Status footer styling */
    .status-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        padding: 0.5rem;
        background-color: #2b2b3a;
        color: #cccccc;
        font-style: italic;
        z-index: 1000;
    }
    
    /* Hide hamburger menu and footer */
    .stDeployButton, footer, #MainMenu {
        visibility: hidden;
    }
    
    /* Custom buttons */
    .stButton > button {
        background-color: #f25a5a;
        color: white;
        border: none;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_question = ""
    st.session_state.status_messages = []
    st.session_state.current_values = {}
    st.session_state.last_question = ""
    st.session_state.processing = False
    st.session_state.generating_answer = False
    st.session_state.items = []

# Custom logo and header
st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <img src="https://raw.githubusercontent.com/streamlit/streamlit/master/frontend/public/favicon.png" width="40">
        <h1 style="margin-left: 10px; color: white;">RAVE - Recursive Agent</h1>
    </div>
""", unsafe_allow_html=True)
st.subheader("Your AI Assistant for Verified Explanations")

# Sidebar
with st.sidebar:
    st.header("Status")
    st.markdown("---")
    
    # New Conversation button
    if st.button("New Conversation"):
        st.session_state.current_question = ""
        st.session_state.status_messages = []
        st.session_state.current_values = {}
        st.session_state.last_question = ""
        st.session_state.processing = False
        st.session_state.generating_answer = False
        st.rerun()
    
    # Display status messages
    for msg in st.session_state.status_messages:
        st.markdown(f'<div class="status-message">{msg}</div>', unsafe_allow_html=True)

# Main interface
question = st.text_input(
    "What would you like to know?",
    value=st.session_state.current_question,
    placeholder="Enter your question here..."
)

# Store the current question in session state
st.session_state.current_question = question

# Main content area
main_container = st.container()

# Process the question when it changes
if question and question != st.session_state.last_question:
    st.session_state.last_question = question
    st.session_state.processing = True
    st.session_state.generating_answer = True
    
    # Clear previous status messages for new question
    st.session_state.status_messages = []
    
    # Initialize display areas
    with main_container:
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
                        st.session_state.status_messages.append(new_message)
                        st.rerun()
                    
                    elif output_type == "values":
                        # Update values in the main area
                        st.session_state.current_values = output_data
                        with values_placeholder:
                            st.json(st.session_state.current_values)
            
            # When processing is complete
            st.session_state.generating_answer = False
            st.session_state.processing = False
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state.generating_answer = False
            st.session_state.processing = False
else:
    # Display current values if they exist
    with main_container:
        if st.session_state.current_values:
            st.markdown("### Output Values")
            st.json(st.session_state.current_values)
            
# Add a status footer for the "Generating answer..." message when needed
if st.session_state.generating_answer:
    st.markdown(
        '<div class="status-footer">Generating answer...</div>', 
        unsafe_allow_html=True
    )