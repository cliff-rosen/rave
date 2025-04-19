import sys
import os
import random
from enum import Enum
import json
from datetime import datetime
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

VERSION = "0.1.2"


# Session management functions
def save_session():
    """Save current session to a file"""
    try:
        # Create a serializable copy of the session data
        
        # Convert the KnowledgeNugget objects to dictionaries
        serializable_values_history = []
        for values_entry in st.session_state.values_history:
            # Create a copy of the entry to avoid modifying the original
            entry_copy = values_entry.copy()
            
            # Handle knowledge_base if it exists
            if "knowledge_base" in entry_copy:
                knowledge_base = entry_copy["knowledge_base"]
                serializable_knowledge_base = []
                for nugget in knowledge_base:
                    try:
                        # Convert Pydantic model to dict using model_dump()
                        nugget_dict = nugget.model_dump()
                        serializable_knowledge_base.append(nugget_dict)
                    except Exception as e:
                        print(f"Error serializing nugget: {e}")
                        continue
                entry_copy["knowledge_base"] = serializable_knowledge_base
            
            serializable_values_history.append(entry_copy)

        session_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H%M%S"),
            "question": st.session_state.current_question,
            "status_messages": st.session_state.status_messages,
            "values_history": serializable_values_history,
            "values_history_description": st.session_state.values_history_description,
            "current_values_idx": st.session_state.current_values_idx,
            "processing_status": st.session_state.processing_status,
            "processing_status_message": st.session_state.processing_status_message,
            "model_settings": {
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
        
        # Create sessions directory if it doesn't exist
        os.makedirs("sessions", exist_ok=True)
        
        # Save to file with proper error handling
        filename = f"sessions/session_{session_data['timestamp']}.json"
        temp_filename = f"{filename}.tmp"
        
        # First write to a temporary file
        with open(temp_filename, "w") as f:
            json.dump(session_data, f, indent=2)
        
        # Verify the temporary file is valid JSON
        with open(temp_filename, "r") as f:
            json.load(f)  # This will raise an error if the JSON is invalid
        
        # If we get here, the JSON is valid, so we can rename the temp file
        if os.path.exists(filename):
            os.remove(filename)
        os.rename(temp_filename, filename)
        
        return filename
    except Exception as e:
        print(f"Error saving session: {e}")
        # Clean up temporary file if it exists
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        raise

def load_session(filename):
    """Load a session from file"""
    try:
        print("loading session", filename)
        with open(filename, "r") as f:
            session_data = json.load(f)
        print("session_data question", session_data["question"])

        # Restore session state
        st.session_state.current_question = session_data["question"]
        st.session_state.status_messages = session_data["status_messages"]
        
        # Convert serialized knowledge_base back to KnowledgeNugget objects
        values_history = []
        for value in session_data["values_history"]:
            # Create a copy of the value to avoid modifying the original
            value_copy = value.copy()
            
            # Handle knowledge_base if it exists
            if "knowledge_base" in value_copy:
                knowledge_base = value_copy["knowledge_base"]
                reconstructed_knowledge_base = []
                for nugget_dict in knowledge_base:
                    # Reconstruct KnowledgeNugget using model_validate
                    from backend.agents.utils.prompts import KnowledgeNugget
                    reconstructed_knowledge_base.append(KnowledgeNugget.model_validate(nugget_dict))
                value_copy["knowledge_base"] = reconstructed_knowledge_base
            
            values_history.append(value_copy)
        
        st.session_state.values_history = values_history
        st.session_state.values_history_description = session_data["values_history_description"]
        st.session_state.current_values_idx = session_data["current_values_idx"]
        st.session_state.processing_status = session_data["processing_status"]
        st.session_state.processing_status_message = session_data["processing_status_message"]
        
        # Restore model settings
        model_settings = session_data["model_settings"]
        st.session_state.question_model = model_settings["question_model"]
        st.session_state.checklist_model = model_settings["checklist_model"]
        st.session_state.query_model = model_settings["query_model"]
        st.session_state.answer_model = model_settings["answer_model"]
        st.session_state.scoring_model = model_settings["scoring_model"]
        st.session_state.kb_model = model_settings["kb_model"]
        st.session_state.max_iterations = model_settings["max_iterations"]
        st.session_state.score_threshold = model_settings["score_threshold"]
        return True
    except Exception as e:
        print("error loading session", e)
        st.error(f"Error loading session: {str(e)}")
        return False

def delete_session(filename):
    """Delete a saved session file"""
    try:
        os.remove(filename)
        return True
    except Exception as e:
        st.error(f"Error deleting session: {str(e)}")
        return False

class ProcessStatus(Enum):
    WAITING_FOR_INPUT = "WAITING FOR INPUT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    ERROR = "ERROR"

### Session Management
def cancel_processing():
    st.session_state.processing_status = ProcessStatus.CANCELED.value
    st.session_state.processing_status_message = "Processing canceled"
    output_control_container()
    output_status_message_area()

def new_conversation():
    st.session_state.current_question = ""
    st.session_state.status_messages = []
    st.session_state.current_values = {}
    st.session_state.values_history = []
    st.session_state.values_history_description = []
    st.session_state.processing_status = ProcessStatus.WAITING_FOR_INPUT.value
    st.session_state.processing_status_message = "Waiting for input..."
    output_control_container()
    output_status_message_area()

### Helper functions

# All output functions write to pre-defined containers
def output_debug_info(output_data):
    with st.session_state.debug_container:
        st.write(output_data)

def output_control_container():
    with st.session_state.control_container:
        st.empty()
        control_container = st.container()
        with control_container:
            st.empty()
            if st.session_state.processing_status != ProcessStatus.WAITING_FOR_INPUT.value:
                st.markdown(st.session_state.current_question)
            
            if st.session_state.processing_status == ProcessStatus.PROCESSING.value:
                st.button("Cancel", key=f"cancel_processing", on_click=cancel_processing)
            
            if st.session_state.processing_status == ProcessStatus.COMPLETED.value or st.session_state.processing_status == ProcessStatus.CANCELED.value:
                st.button("New Conversation", key=f"new_conversation_{random.randint(0, 1000000)}", on_click=new_conversation)

def output_values(output_data):
    output_debug_info(output_data)
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
            st.markdown(output_data["answer"])
    
    with st.session_state.scored_checklist_container:
        if "scored_checklist" in output_data and output_data["scored_checklist"]:
            scorecard_container = st.container()
            with scorecard_container:
                # Calculate average score
                total_score = 0
                for item in output_data["scored_checklist"]:
                    total_score += item.get("current_score", 0)
                avg_score = total_score / len(output_data["scored_checklist"])
                
                # Display average score at the top
                st.markdown(f"### Overall Score: {avg_score:.2f}")
                st.progress(avg_score)
                st.markdown("---")
                
                # Display individual items in two columns
                for item in output_data["scored_checklist"]:
                    score = item.get("current_score", 0)
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(item.get("item_to_score", ""))
                    with col2:
                        st.progress(score)

def output_currently_selected_values():
    if st.session_state.current_values_idx is not None and 0 <= st.session_state.current_values_idx < len(st.session_state.values_history):
        idx = st.session_state.current_values_idx
        output_debug_info(st.session_state.values_history[idx])
        output_values(st.session_state.values_history[idx])

def output_values_for_selected_idx(idx):
    st.session_state.current_values_idx = idx
    output_debug_info(idx)

    if 0 <= idx < len(st.session_state.values_history):
        output_values(st.session_state.values_history[idx])
    else:
        print("selected_status index out of range", idx)

def output_status_message_area():
    # Display status messages in a table format
    with st.session_state.values_history_container:
        st.empty()
        message_container = st.container(height=900)
        with message_container:
            status_container = st.container(height=150)
            with status_container:
                st.write("STATUS:")
                st.write(st.session_state.processing_status_message)

            values_container = st.container(height=700)
            with values_container:
                st.write("TIME TRAVEL:")
                if st.session_state.values_history_description:
                    for i in range (len(st.session_state.values_history_description)):
                        with st.expander(st.session_state.values_history_description[i], expanded=False):
                            st.button(
                                label="view tabs as this time",
                                key=f"msg_{i}.{random.randint(0, 1000000)}",
                                on_click=output_values_for_selected_idx,
                                args=(i,),
                                use_container_width=True
                            )
                    
                    if st.session_state.processing_status == ProcessStatus.PROCESSING.value:
                        st.markdown(f"""
                            <div class="processing-status">
                                <div class="processing-dot"></div>
                                <span>{st.session_state.processing_status_message}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write(st.session_state.processing_status)

def output_workflow_visualization():
    """Create a workflow visualization using SVG files"""
    
    with st.session_state.workflow_container:
        st.empty()
        
        # Get current stage based on status messages
        current_stage = 0  # Default to first stage
        if st.session_state.processing_status != ProcessStatus.CANCELED.value and st.session_state.status_messages:
            last_message = st.session_state.status_messages[-1].lower()
            if "improving question" in last_message:
                current_stage = 1
            elif "generating answer requirements" in last_message:
                current_stage = 2
            elif "generating search query" in last_message:
                current_stage = 3
            elif "performing search" in last_message:
                current_stage = 4
            elif "updating knowledge base" in last_message:
                current_stage = 5
            elif "generating answer" in last_message:
                current_stage = 6
            elif "scoring answer" in last_message:
                current_stage = 7
            elif "evaluating whether to continue" in last_message:
                current_stage = 8
            elif st.session_state.processing_status == ProcessStatus.COMPLETED.value:
                current_stage = 8  # Show done state when processing is completed

        # Load the appropriate SVG file
        svg_file = f"frontend/assets/workflow/state_{current_stage}_"
        svg_file += {
            0: "initial",
            1: "improve",
            2: "checklist",
            3: "query",
            4: "search",
            5: "kb",
            6: "answer",
            7: "evaluate",
            8: "done"
        }[current_stage] + ".svg"
        
        try:
            with open(svg_file, 'r') as f:
                svg_content = f.read()
                
            # Create container div for proper sizing
            html = f'''
            <div style="width:100%;height:80px;overflow:hidden;">
                {svg_content}
            </div>
            '''
            
            st.components.v1.html(html, height=80)
        except Exception as e:
            st.error(f"Error loading workflow visualization: {str(e)}")

# Update functions are reactive by calling output_values which writes to pre-defined containers
def update_values(output_data):
    # print("update_values", output_data)
    output_data_copy = copy.deepcopy(output_data)
    description = ""
    if len(st.session_state.status_messages) > 0:
        description = st.session_state.status_messages[-1]
    else:
        description = "Initial values"
    st.session_state.current_values = output_data_copy
    st.session_state.values_history.append(output_data_copy)
    st.session_state.values_history_description.append(description)
    output_values(output_data_copy)

def update_status_messages(message_text):
    st.session_state.status_messages.append(message_text)
    st.session_state.processing_status_message = message_text
    output_status_message_area()

def agent_process():
    print("agent_process: " + st.session_state.current_question)

    initial_state = {
        "messages": [],
        "question": st.session_state.current_question,
        "improved_question": "",
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

            output_workflow_visualization()

    st.session_state.current_values_idx = len(st.session_state.values_history) - 1

def handle_question_input():
    st.session_state.current_question = st.session_state.question_input
    st.session_state.processing_status = ProcessStatus.PROCESSING.value
    output_control_container()
    agent_process()
    st.session_state.processing_status = ProcessStatus.COMPLETED.value


### Initialize session state variables
if 'initialized' not in st.session_state:
    # Initialized
    st.session_state.initialized = True

    # State
    st.session_state.current_question = ""  # gathered from user
    st.session_state.status_messages = []  # messages from the agent
    st.session_state.current_values = {}  # current values of the agent 
    st.session_state.values_history = []  # history of values
    st.session_state.values_history_description = []  # description of the values
    st.session_state.current_values_idx = None
    st.session_state.debug_message = "-"

    # Processing status
    st.session_state.processing_status = ProcessStatus.WAITING_FOR_INPUT.value
    st.session_state.processing_status_message = "Waiting for input..."
    st.session_state.should_rerun = False

    # Initialize containers
    st.session_state.control_container = None
    st.session_state.improved_question_container = None
    st.session_state.query_container = None
    st.session_state.query_history_container = None
    st.session_state.search_res_container = None
    st.session_state.kb_container = None
    st.session_state.answer_container = None
    st.session_state.scored_checklist_container = None
    st.session_state.debug_container = None
    st.session_state.values_history_container = None
    st.session_state.workflow_container = None

    # Initialize settings
    st.session_state.question_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.checklist_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.query_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.answer_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.scoring_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.kb_model = OpenAIModel.GPT4O.value["name"]
    st.session_state.max_iterations = 3
    st.session_state.score_threshold = 0.9

### START OF OUTPUT ###

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


### Create layout

# Settings Sidebar
with st.sidebar:
    st.title("Settings")
    st.write(f"Version: {VERSION}")

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

    # Session Management
    st.markdown("---")
    st.subheader("Session Management")
    
    # Save current session
    if st.session_state.processing_status == ProcessStatus.COMPLETED.value:
        if st.button("Save Current Session"):
            filename = save_session()
            st.success(f"Session saved to {filename}")
    
    # List and load saved sessions
    st.subheader("Saved Sessions")
    sessions_dir = "sessions"
    if os.path.exists(sessions_dir):
        session_files = sorted([f for f in os.listdir(sessions_dir) if f.endswith(".json")], reverse=True)
        for session_file in session_files:
            with st.expander(session_file):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # if st.button("Load Session", key=f"load_{session_file}"):
                    #     if load_session(os.path.join(sessions_dir, session_file)):
                    #         st.success("Session loaded successfully")
                    #         st.rerun()
                    if st.button("Load Session", key=f"load_{session_file}", on_click=lambda session_file=session_file: load_session(os.path.join(sessions_dir, session_file))):
                        st.success("Session loaded successfully")
                        st.rerun()
                with col2:
                    if st.button("Del", key=f"delete_{session_file}"):
                        if delete_session(os.path.join(sessions_dir, session_file)):
                            st.success("Session deleted successfully")
                            st.rerun()
    else:
        st.info("No saved sessions found")

# Create two columns: left for input and right for content
left_col, right_col = st.columns([1, 2])

# Left column for input and controls
with left_col:
    # Header
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <img src="https://raw.githubusercontent.com/streamlit/streamlit/master/frontend/public/favicon.png" width="40">
            <h1 style="margin-left: 10px; color: white;">RAVE</h1>
        </div>
    """, unsafe_allow_html=True)
    st.subheader("Your RecursiveAI Assistant for Verified Explanations")
    st.markdown("---")

    # Control container 
    st.session_state.control_container = st.empty()
    output_control_container()

    # Question input    
    question = st.text_input(
        "What would you like to know?",
        key="question_input",
        value=st.session_state.current_question,
        placeholder="Enter your question here...",
        on_change=handle_question_input
    )
        
    # Status messages area
    # st.markdown("### Process Updates")
    st.session_state.values_history_container = st.empty()
   
# Right column with tabs
with right_col:
    # Create workflow container at the top
    st.session_state.workflow_container = st.empty()
    output_workflow_visualization()
    
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

output_currently_selected_values()
output_status_message_area()
st.write("st.session_state.score_threshold", st.session_state.score_threshold)
st.write("st.session_state.kb_model", st.session_state.kb_model)

