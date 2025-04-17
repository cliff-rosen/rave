import streamlit as st
from backend.agents.rave_agent import graph
from backend.config.models import OpenAIModel, get_model_config
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

### Initialize session state variables
if 'initialized' not in st.session_state:
    # Initialized
    st.session_state.initialized = True

    # State
    st.session_state.current_question = ""
    st.session_state.improved_question = ""
    st.session_state.current_query = ""
    st.session_state.query_history = []
    st.session_state.search_results = []
    st.session_state.knowledge_base = []
    st.session_state.answer = ""
    st.session_state.scored_checklist = []
    st.session_state.status_messages = []
    st.session_state.current_values = {}
    st.session_state.values_history = []
    st.session_state.last_question = ""

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
    </style>
    """, unsafe_allow_html=True)


### Helper functions

def output_history(output_data):
    with st.session_state.history_container:
        st.json(output_data)

def output_debug_info(output_data):
    print("****************************")
    print("output_debug_info", output_data)
    print("****************************")
    with st.session_state.debug_container:
        st.json(output_data)

def output_values(output_data):
    # print("output_values", output_data)

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

def update_history(output_data):
    print("update_history before update", st.session_state.values_history)
    st.session_state.values_history.append(output_data)
    print("update_history after update", st.session_state.values_history)
    output_history(st.session_state.values_history)

def update_values(output_data):
    st.session_state.current_values = output_data
    update_history(output_data)
    output_values(output_data)

def output_status_messages():
    # Display the radio selection with original messages
    with st.session_state.status_container:
        selected_status = st.radio(
            "Process Updates",
            options= [message["message"] + " [" + str(message["update_idx"]) + "]" for message in st.session_state.status_messages],
            index=len(st.session_state.status_messages) - 1 if st.session_state.status_messages else 0,
            label_visibility="collapsed",
            key=f"status_container_radio_{len(st.session_state.status_messages)}"
        )
        
        # If a status is selected, show the corresponding values
        if selected_status:
            print("selected_status", selected_status)
            idx = int(selected_status[selected_status.index("[") + 1:selected_status.index("]")])
            if 0 <= idx < len(st.session_state.values_history):
                output_values(st.session_state.values_history[idx])
                output_debug_info(st.session_state.values_history[idx])
            else:
                print("selected_status index out of range", idx)
                output_debug_info(st.session_state.values_history[0])

# store messages as list of {"update_idx": value_update_idx, "message": message}
def update_status_messages(message):
    update_idx = len(st.session_state.values_history)
    message = {"update_idx": update_idx, "message": message}
    st.session_state.status_messages.append(message)
    output_status_messages()
    output_history(st.session_state.values_history)

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
        print("****************************")
        print("values history[0] at start of output processing", st.session_state.values_history[0] if len(st.session_state.values_history) > 0 else "empty")
        print("values history[-1] at start of output processing", st.session_state.values_history[-1] if len(st.session_state.values_history) > 0 else "empty")
        if isinstance(output, tuple):
            output_type, output_data = output
            
            if output_type == "custom":
                # Add new status message
                update_status_messages(output_data.get("msg", ""))
            
            elif output_type == "values":
                # Update values in the main area
                update_values(output_data)
        print("****************************")
        print("****************************")
        print("values history[0] at end of output processing", st.session_state.values_history[0] if len(st.session_state.values_history) > 0 else "empty")


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

left_col, search_col, kb_col, answer_col, score_col, history_col = st.columns([1, 2, 2, 2, 2, 2])

# Search column - Query and search results
with search_col:
    st.header("Search")
    st.markdown("---")

    # Improved question display
    st.markdown("### Improved Question")
    st.session_state.improved_question_container = st.empty()

    # Current query
    st.markdown("### Current Query")
    st.session_state.query_container = st.empty()
    
    # Query history
    st.markdown("### Query History")
    st.session_state.query_history_container = st.empty()
    
    # Search results
    st.markdown("### Search Results")
    st.session_state.search_res_container = st.empty()

# Knowledge Base column
with kb_col:
    st.header("Knowledge Base")
    st.markdown("---")
    st.session_state.kb_container = st.empty()

# Answer column
with answer_col:
    st.header("Answer")
    st.markdown("---")
    st.session_state.answer_container = st.empty()

# Scorecard column
with score_col:
    st.header("Scorecard")
    st.markdown("---")
    st.session_state.scored_checklist_container = st.empty()

with history_col:
    st.header("History")
    st.markdown("---")
    st.session_state.history_container = st.empty()

# Left column last because of dependency on other columns
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
            st.session_state.last_question = ""
            st.session_state.processing_status = "WAITING FOR INPUT"
            st.session_state.generating_answer = False
            st.session_state.should_rerun = True
            st.session_state.cancelled = False
            st.experimental_rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.cancelled = True
            st.session_state.processing_status = "CANCELLING"
            st.session_state.generating_answer = False
            st.write("Cancelled")
            # update_status_messages("Cancelled by user")
            output_values(st.session_state.current_values)
            output_history(st.session_state.values_history)

    if st.button("go"):
        print("go")
        st.write("go2")
        with st.session_state.improved_question_container:
            st.write("improved_question")
        with st.session_state.debug_container:
            st.write("debug")

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

# # Force rerun if needed
# if st.session_state.should_rerun:
#     st.session_state.should_rerun = False
#     st.experimental_rerun()