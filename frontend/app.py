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
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.initialized = True
    st.session_state.history = []
    st.session_state.current_query = ""
    st.session_state.current_response = ""

# Header
st.title("🤖 RAVE - Recursive Agent")
st.subheader("Your AI Assistant for Verified Explanations")

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.markdown("---")
    
    # Reset button
    if st.button("New Conversation", type="primary"):
        st.session_state.history = []
        st.session_state.current_query = ""
        st.session_state.current_response = ""
        st.rerun()

# Main interface
query = st.text_input(
    "What would you like to know?",
    key="current_query",
    placeholder="Enter your question here..."
)

if query and query != st.session_state.get("last_query", ""):
    st.session_state.last_query = query
    
    # Initialize progress tracking
    progress_placeholder = st.empty()
    response_placeholder = st.empty()
    
    # Initialize state for the agent
    initial_state = {
        "messages": [],
        "query": query,
        "scorecard": None,
        "search_history": {"queries": [], "results": []},
        "attempt_history": {"responses": [], "scores": [], "feedback": []},
        "current_gaps": [],
        "current_attempt": None,
        "new_queries": [],
        "search_results": []
    }
    
    # Process with the agent
    try:
        for output in graph.stream(initial_state):
            # Update progress based on the current step
            if isinstance(output, tuple):
                output_type, output_data = output
                if output_type == "updates":
                    with progress_placeholder:
                        st.write(f"Processing: {output_data}")
                elif output_type == "final":
                    final_response = output_data.get("current_attempt", "No response generated")
                    with response_placeholder:
                        st.markdown(final_response)
                        
                        # Show evaluation if available
                        if output_data.get("scorecard"):
                            with st.expander("Response Evaluation"):
                                st.json(output_data["scorecard"])
                        
                        # Add to history
                        st.session_state.history.append({
                            "query": query,
                            "response": final_response,
                            "scorecard": output_data.get("scorecard")
                        })
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Show conversation history
if st.session_state.history:
    st.markdown("---")
    st.subheader("Conversation History")
    for idx, item in enumerate(reversed(st.session_state.history)):
        with st.expander(f"Q: {item['query'][:50]}..."):
            st.markdown(item["response"])
            if item.get("scorecard"):
                st.json(item["scorecard"]) 