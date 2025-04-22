import streamlit as st
import time
from backend.agents.rave_agent import search2, get_best_urls_from_search

state = {
    "question": "i'd like to better understand how the economy works",
    "improved_question": "i'd like to better understand how the economy works",
    "current_query": "are tarrifs good or bad for the economy?",
    "search_results": [],
    "urls_to_scrape": [],
    "scraped_content": []
}

if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.state = state

st.button("refresh")

def search():
    st.session_state.search_status = "searching..."
    st.session_state.search_results = []
    st.session_state.urls_to_scrape = []

    st.session_state.search_status_container.write("searching...")
    st.session_state.state["current_query"] = st.session_state.query
    print("state", st.session_state.state)
    res = search2(
            st.session_state.state,
            writer=None,
            config={"configurable": {"max_search_results": 4}}
        )
    st.session_state.state_container.empty()
    st.session_state.state_container.write("search completed")
    st.session_state.state["search_results"] = res["search_results"]

def get_urls():
    st.session_state.search_status_container.write("getting best urls...")
    res = get_best_urls_from_search(
        st.session_state.state,
        writer=None,
        config={"configurable": {"max_search_results": 4}}
    )
    st.session_state.state_container.empty()
    st.session_state.state_container.write("urls retrieved")
    st.session_state.state["urls_to_scrape"] = res["urls_to_scrape"]


left_col, right_col = st.columns([1,4])

with left_col:
    st.text_input("question", on_change=search, key="query")
    st.session_state.search_status_container = st.empty()
    st.write("get urls")
    st.button("get urls", on_click=get_urls)

with right_col:
    st.write("state")
    st.session_state.state_container = st.empty()
    st.session_state.state_container.write(st.session_state.state)


