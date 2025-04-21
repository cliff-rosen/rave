import streamlit as st
import time
from backend.agents.rave_agent import search2


state = {
    "question": "my question",
    "current_query": "",
    "search_results": [],
    "urls_to_scrape": [],
    "scraped_content": []
}

def search():
    st.session_state.search_status = "searching..."
    st.session_state.search_results = []
    st.session_state.urls_to_scrape = []

    st.session_state.search_status_container.write("searching...")
    state["current_query"] = st.session_state.question
    print("state", state)
    res = search2(
            state,
            writer=None,
            config={"configurable": {"max_search_results": 4}}
        )
    st.session_state.search_status_container.empty()
    print("res", res)
    st.session_state.search_results = res["search_results"]
    st.session_state.search_status = "search completed"

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.question = "my question"
    st.session_state.search_results = []
    st.session_state.urls_to_scrape = []
    st.session_state.scraped_content = []


st.button("refresh")

st.text_input("question", on_change=search, key="question")

st.write("search results")
st.session_state.search_status_container = st.empty()
search_status_container = st.empty()

st.json(st.session_state.search_results)


