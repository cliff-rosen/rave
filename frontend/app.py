import sys
import os
import random
# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import streamlit as st
from backend.agents.rave_agent import graph
from backend.config.models import OpenAIModel, get_model_config
import time
import copy
from backend.config.settings import MAX_ITERATIONS, OPENAI_API_KEY, TAVILY_API_KEY
import pandas as pd


### Initialize session state variables
if 'initialized' not in st.session_state:
    # Initialized
    st.session_state.initialized = True

    # State
    st.session_state.current_question = ""  # gathered from user
    st.session_state.status_messages = []  # messages from the agent
    st.session_state.current_values = {}  # current values of the agent 
    st.session_state.values_history = []  # history of values
    st.session_state.current_values_idx = 0

    # Processing status
    st.session_state.processing_status = "WAITING FOR INPUT"
    st.session_state.generating_answer = False
    st.session_state.should_rerun = False
    st.session_state.cancelled = False

    # Containers
    st.session_state.improved_question_container = None
    st.session_state.query_container = None
    st.session_state.query_history_container = None
    st.session_state.search_res_container = None
    st.session_state.kb_container = None
    st.session_state.answer_container = None
    st.session_state.scored_checklist_container = None
    st.session_state.debug_container = None

    # Initialize settings
    st.session_state.question_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.checklist_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.query_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.answer_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.scoring_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.kb_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.max_iterations = 3
    st.session_state.score_threshold = 0.9

### Page configuration
st.set_page_config(
    page_title="RAVE - Recursive Agent for Verified Explanations",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply dark theme and custom styling
st.markdown("""
    <style>
    /* Dark theme */
    :root {
        --background-color: #1e1e2e;
        --text-color: #ffffff;
        --status-bg-color: #2b2b3a;
    }
    
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
        padding: 1rem;
    }
    
    header {
        background-color: var(--background-color);
        visibility: xhidden;
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
        visibility: xhidden;
    }
    
    /* Custom buttons */
    .stButton > button {
        background-color: #f25a5a;
        color: white;
        border: none;
        font-weight: bold;
    }

    /* Status message buttons */
    .status-message-button {
        background-color: #2b2b3a !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #cccccc !important;
        font-weight: normal !important;
        text-align: left !important;
        padding: 0.5rem 1rem !important;
        margin: 0.25rem 0 !important;
        border-radius: 0.25rem !important;
        transition: all 0.2s ease !important;
    }

    .status-message-button:hover {
        background-color: #3b3b4a !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* Processing animation */
    .processing-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .processing-dot {
        width: 8px;
        height: 8px;
        background-color: #f25a5a;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% {
            transform: scale(0.95);
            opacity: 0.5;
        }
        50% {
            transform: scale(1.1);
            opacity: 1;
        }
        100% {
            transform: scale(0.95);
            opacity: 0.5;
        }
    }
    </style>
    """, unsafe_allow_html=True)


### Helper functions

# All output functions write to pre-defined containers
def output_debug_info(output_data):
    with st.session_state.debug_container:
        st.write(output_data)

def output_values(output_data):

    # Update all containers with their respective values
    with st.session_state.improved_question_container:
        if "improved_question" in output_data:
            st.write(output_data["improved_question"])
    
    with st.session_state.query_container:
        if "current_query" in output_data:
            st.write(output_data["current_query"])
    
    with st.session_state.query_history_container:
        if "query_history" in output_data:
            st.json({"query_history": output_data["query_history"]})
    
    with st.session_state.search_res_container:
        if "search_results" in output_data:
            st.json({"search_results": output_data["search_results"]})
    
    with st.session_state.kb_container:
        if "knowledge_base" in output_data:
            st.json({"knowledge_base": output_data["knowledge_base"]})
    
    with st.session_state.answer_container:
        if "answer" in output_data:
            # Display answer in markdown format
            st.markdown(output_data["answer"])
    
    with st.session_state.scored_checklist_container:
        if "scored_checklist" in output_data:
            st.json({"scored_checklist": output_data["scored_checklist"]})

def output_currently_selected_values():
    if st.session_state.current_values_idx is not None and 0 <= st.session_state.current_values_idx < len(st.session_state.values_history):
        idx = st.session_state.current_values_idx
        output_debug_info(st.session_state.values_history[idx])
        output_values(st.session_state.values_history[idx])

def output_values_for_selected_status(idx):
    st.session_state.current_values_idx = idx
    output_debug_info(idx)

    if 0 <= idx < len(st.session_state.values_history):
        output_values(st.session_state.values_history[idx])
    else:
        print("selected_status index out of range", idx)

def output_status_messages():
    # Display status messages in a table format
    with st.session_state.status_container:
        st.empty()
        message_container = st.container()
        with message_container:
            if st.session_state.status_messages:
                for msg in st.session_state.status_messages:
                    # Use expander for each message
                    with st.expander(msg["message"], expanded=False):
                        st.button(
                            label="View Details",
                            key=f"msg_{msg['update_idx']}.{random.randint(0, 1000000)}",
                            on_click=output_values_for_selected_status,
                            args=(msg["update_idx"],),
                            use_container_width=True
                        )
                
                # Show animated status
                if st.session_state.processing_status == "PROCESSING":
                    st.markdown("""
                        <div class="processing-status">
                            <div class="processing-dot"></div>
                            <span>Processing...</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(st.session_state.processing_status)

# Update functions are reactive by calling output_values which writes to pre-defined containers
def update_values(output_data):
    output_data_copy = copy.deepcopy(output_data)
    st.session_state.current_values = output_data_copy
    st.session_state.values_history.append(output_data_copy)
    output_values(output_data_copy)

# store messages as list of {"update_idx": value_update_idx, "message": message}
def update_status_messages(message_text):
    update_idx = len(st.session_state.values_history) - 1
    message = {"update_idx": update_idx, "message": message_text}
    st.session_state.status_messages.append(message)
    output_status_messages()

def agent_process(question):
    initial_state = {
        "messages": [],
        "question": question,
        "scored_checklist": [],
        "current_query": None,
        "query_history": [],
        "search_results": [],
        "knowledge_base": [],
        "answer": None,
    }

    # Create config with model settings
    config = {
        "configurable": {
            "question_model": st.session_state.question_model,
            "checklist_model": st.session_state.checklist_model,
            "query_model": st.session_state.query_model,
            "answer_model": st.session_state.answer_model,
            "scoring_model": st.session_state.scoring_model,
            "kb_model": st.session_state.kb_model,
            "max_iterations": st.session_state.max_iterations,
            "score_threshold": st.session_state.score_threshold
        }
    }

    # Process with the agent
    for output in graph.stream(initial_state, config=config, stream_mode=["values", "custom"]):
        if isinstance(output, tuple):
            output_type, output_data = output
            if output_type == "custom":
                # Add new status message
                update_status_messages(output_data.get("msg", ""))

            elif output_type == "values":
                # Update values in the main area
                update_values(output_data)


### Create layout

# Settings Sidebar
with st.sidebar:
    st.title("Settings")
    
    st.subheader("Model Selection")
    st.session_state.question_model = st.selectbox(
        "Question Improvement Model",
        options=[model.value["name"] for model in OpenAIModel],
        index=[model.value["name"] for model in OpenAIModel].index(st.session_state.question_model)
    )
    
    st.session_state.checklist_model = st.selectbox(
        "Checklist Generation Model",
        options=[model.value["name"] for model in OpenAIModel],
        index=[model.value["name"] for model in OpenAIModel].index(st.session_state.checklist_model)
    )
    
    st.session_state.query_model = st.selectbox(
        "Query Generation Model",
        options=[model.value["name"] for model in OpenAIModel],
        index=[model.value["name"] for model in OpenAIModel].index(st.session_state.query_model)
    )
    
    st.session_state.answer_model = st.selectbox(
        "Answer Generation Model",
        options=[model.value["name"] for model in OpenAIModel],
        index=[model.value["name"] for model in OpenAIModel].index(st.session_state.answer_model)
    )
    
    st.session_state.scoring_model = st.selectbox(
        "Scoring Model",
        options=[model.value["name"] for model in OpenAIModel],
        index=[model.value["name"] for model in OpenAIModel].index(st.session_state.scoring_model)
    )
    
    st.session_state.kb_model = st.selectbox(
        "Knowledge Base Model",
        options=[model.value["name"] for model in OpenAIModel],
        index=[model.value["name"] for model in OpenAIModel].index(st.session_state.kb_model)
    )
    
    st.subheader("Graph Settings")
    st.session_state.max_iterations = st.slider(
        "Maximum Iterations",
        min_value=1,
        max_value=10,
        value=st.session_state.max_iterations,
        step=1
    )
    
    st.session_state.score_threshold = st.slider(
        "Score Threshold",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.score_threshold,
        step=0.05
    )

# Create two columns: left for input and right for content
left_col, right_col = st.columns([1, 2])

# Left column for input and controls
with left_col:
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <img src="https://raw.githubusercontent.com/streamlit/streamlit/master/frontend/public/favicon.png" width="40">
            <h1 style="margin-left: 10px; color: white;">RAVE - Recursive Agent</h1>
        </div>
    """, unsafe_allow_html=True)
    st.subheader("Your AI Assistant for Verified Explanations")
    st.markdown("---")

    # Buttons for new conversation and cancel
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Conversation"):
            st.session_state.current_question = ""
            st.session_state.status_messages = []
            st.session_state.current_values = {}
            st.session_state.values_history = []
            st.session_state.processing_status = "WAITING FOR INPUT"
            st.session_state.generating_answer = False
            st.session_state.should_rerun = True
            st.session_state.cancelled = False
    with col2:
        if st.button("Cancel"):
            st.session_state.cancelled = True
            st.session_state.processing_status = "CANCELLING"
            st.session_state.generating_answer = False
            st.write("Cancelled")
            output_values(st.session_state.current_values)

    # Question input
    question = st.text_input(
        "What would you like to know?",
        value=st.session_state.current_question,
        placeholder="Enter your question here..."
    )
    
    # Store the current question in session state
    st.session_state.current_question = question
    
    # Status messages area
    st.markdown("### Process Updates")
    st.session_state.status_container = st.empty()
    
    # Display all current status messages
    output_status_messages()

# Right column with tabs
with right_col:
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Search", "Knowledge Base", "Answer", "Scorecard"])
    
    # Search tab
    with tab1:
        st.markdown("### Improved Question")
        st.session_state.improved_question_container = st.empty()

        st.markdown("### Current Query")
        st.session_state.query_container = st.empty()
        
        st.markdown("### Query History")
        st.session_state.query_history_container = st.empty()
        
        st.markdown("### Search Results")
        st.session_state.search_res_container = st.empty()
    
    # Knowledge Base tab
    with tab2:
        st.session_state.kb_container = st.empty()
    
    # Answer tab
    with tab3:
        st.session_state.answer_container = st.empty()
    
    # Scorecard tab
    with tab4:
        st.session_state.scored_checklist_container = st.empty()

st.header("Debug")
st.markdown("---")
if st.session_state.debug_container is None:
    st.session_state.debug_container = st.empty()

### Main processing

# Set processing state if we have a new question
if question and st.session_state.processing_status == "WAITING FOR INPUT":

    st.session_state.processing_status = "PROCESSING"
    st.session_state.generating_answer = True
    st.session_state.cancelled = False
    st.session_state.status_messages = []

    agent_process(st.session_state.current_question)

    st.session_state.generating_answer = False
    st.session_state.processing_status = "COMPLETED"
    # st.rerun()


# Add a status footer for the "Generating answer..." message when needed
if st.session_state.generating_answer:
    st.markdown(
        '<div class="status-footer">Generating answer...</div>', 
        unsafe_allow_html=True
    )

output_currently_selected_values()