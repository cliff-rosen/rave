import streamlit as st
import time

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
    st.session_state.improved_question_container = None
    st.session_state.query_container = None
    st.session_state.query_history_container = None
    st.session_state.search_res_container = None
    st.session_state.kb_container = None
    st.session_state.answer_container = None
    st.session_state.scored_checklist_container = None

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

def output_debug_info(output_data):
    with st.session_state.debug_container:
        st.json(output_data)

def output_values(output_data):
    print("output_values", output_data)
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

def update_values(output_data):
    st.session_state.current_values = output_data
    st.session_state.values_history.append(output_data)
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
            output_data = {"improved_question": "improved_question", "current_query": "current_query", "query_history": "query_history", "search_results": "search_results", "knowledge_base": "knowledge_base", "answer": "answer", "scored_checklist": "scored_checklist"}
            output_values(output_data)
            output_debug_info(output_data)

# store messages as list of {"update_idx": value_update_idx, "message": message}
def update_status_messages(message):
    update_idx = len(st.session_state.values_history)
    message = {"update_idx": update_idx, "message": message}
    st.session_state.status_messages.append(message)
    output_status_messages()

### Create layout


left_col, search_col, kb_col, answer_col, score_col = st.columns([1, 2, 2, 2, 2])

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


    if st.button("go"):
        st.write("go")
        # update_status_messages("Cancelled by user")
        # output_values(st.session_state.current_values)
        #st.experimental_rerun()

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


st.header("Debug")
st.markdown("---")
if "debug_container" not in st.session_state:
    st.session_state.debug_container = st.empty()

### Main processing

# Set processing state if we have a new question
if question:

    update_status_messages("Processing question: " + st.session_state.current_question)

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