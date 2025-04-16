import streamlit as st
from backend.agents.rave_agent import graph
from backend.config.models import OpenAIModel, get_model_config
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

### Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_question = ""
    st.session_state.status_messages = []
    st.session_state.current_values = {}
    st.session_state.values_history = []
    st.session_state.last_question = ""
    st.session_state.processing_status = "WAITING FOR INPUT"
    st.session_state.generating_answer = False
    st.session_state.should_rerun = False
    st.session_state.cancelled = False
    st.session_state.button_container = None
    st.session_state.status_container = None
    
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
    initial_sidebar_state="collapsed",
    menu_items=None
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
        visibility: hidden;
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


### Helper functions

def output_history():
    with st.session_state.history_container:
        if st.session_state.values_history:
            st.json(st.session_state.values_history)
        else:
            st.text("No history yet")

def output_values(output_data):
    
    # Update all containers with their respective values
    with st.session_state.improved_question_container:
        if "improved_question" in output_data:
            st.json({"improved_question": output_data["improved_question"]})
    
    with st.session_state.query_container:
        if "current_query" in output_data:
            st.json({"current_query": output_data["current_query"]})
    
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
            st.json({"answer": output_data["answer"]})
    
    with st.session_state.scored_checklist_container:
        if "scored_checklist" in output_data:
            st.json({"scored_checklist": output_data["scored_checklist"]})

def update_values(output_data):
    st.session_state.current_values = output_data
    st.session_state.values_history.append(output_data)
    output_values(output_data)
    output_history()

def output_status_messages():
    # Display the radio selection with original messages
    with st.session_state.status_container:
        selected_status = st.radio(
            "Process Updates",
            options=st.session_state.status_messages,
            index=len(st.session_state.status_messages) - 1 if st.session_state.status_messages else 0,
            label_visibility="collapsed"
        )
        
        # If a status is selected, show the corresponding values
        if selected_status:
            # Extract the index from the selected status (it's already in [n] format)
            idx = int(selected_status[1:selected_status.index(']')])
            if 0 <= idx < len(st.session_state.values_history):
                output_values(st.session_state.values_history[idx])
                output_history()

def update_status_messages(message):
    value_update_idx = len(st.session_state.values_history)
    message = "[" + str(value_update_idx) + "] " + message
    st.session_state.status_messages.append(message)
    output_status_messages()

def agent_process(question):
    initial_state = {
        "messages": [],
        "question": question,
        "improved_question": None,
        "current_query": None,
        "query_history": [],
        "search_results": [],
        "scored_checklist": [],
        "answer": None,
        "knowledge_base": []
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

left_col, search_col, kb_col, answer_col, score_col, history_col = st.columns([1, 2, 2, 2, 2, 1])

# Left column - Header, title, question input, and process updates
with left_col:
    # Custom logo and header
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <img src="https://raw.githubusercontent.com/streamlit/streamlit/master/frontend/public/favicon.png" width="40">
            <h1 style="margin-left: 10px; color: white;">RAVE - Recursive Agent</h1>
        </div>
    """, unsafe_allow_html=True)
    st.subheader("Your AI Assistant for Verified Explanations")
    st.markdown("---")
    
    if st.button("Cancel"):
        st.session_state.cancelled = True
        st.session_state.processing_status = "CANCELLING"
        st.session_state.generating_answer = False
        st.write("Cancelled")
        update_status_messages("Cancelled by user")
        output_values(st.session_state.current_values)
        #st.experimental_rerun()

    # New Conversation button
    if st.button("New Conversation"):
        st.session_state.current_question = ""
        st.session_state.status_messages = []
        st.session_state.current_values = {}
        st.session_state.values_history = []
        st.session_state.last_question = ""
        st.session_state.processing_status = "WAITING FOR INPUT"
        st.session_state.generating_answer = False
        st.session_state.should_rerun = True
        st.session_state.cancelled = False
        st.experimental_rerun()
    
    # Question input
    question = st.text_input(
        "What would you like to know?",
        value=st.session_state.current_question,
        placeholder="Enter your question here..."
    )
    
    # Store the current question in session state
    st.session_state.current_question = question
    
    # Improved question display
    st.markdown("### Improved Question")
    st.session_state.improved_question_container = st.empty()
    
    # Status messages area
    st.markdown("### Process Updates")
    st.session_state.status_container = st.empty()
    
    # Display all current status messages
    output_status_messages()

# Search column - Query and search results
with search_col:
    st.header("Search")
    st.markdown("---")
    
    # Current query
    st.markdown("### Current Query")
    if "query_container" not in st.session_state:
        st.session_state.query_container = st.empty()
    
    # Query history
    st.markdown("### Query History")
    if "query_history_container" not in st.session_state:
        st.session_state.query_history_container = st.empty()
    
    # Search results
    st.markdown("### Search Results")
    if "search_res_container" not in st.session_state:
        st.session_state.search_res_container = st.empty()

# Knowledge Base column
with kb_col:
    st.header("Knowledge Base")
    st.markdown("---")
    if "kb_container" not in st.session_state:
        st.session_state.kb_container = st.empty()

# Answer column
with answer_col:
    st.header("Answer")
    st.markdown("---")
    if "answer_container" not in st.session_state:
        st.session_state.answer_container = st.empty()

# Scorecard column
with score_col:
    st.header("Scorecard")
    st.markdown("---")
    if "scored_checklist_container" not in st.session_state:
        st.session_state.scored_checklist_container = st.empty()

# Values History column
with history_col:
    st.header("History")
    st.markdown("---")
    if "history_container" not in st.session_state:
        st.session_state.history_container = st.empty()


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

# Force rerun if needed
if st.session_state.should_rerun:
    st.session_state.should_rerun = False
    st.experimental_rerun()