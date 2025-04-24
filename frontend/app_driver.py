import streamlit as st
import time
from backend.agents.rave_agent import search2, get_best_urls_from_search, scrape_urls

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
    st.session_state.cur_idx = 0

if st.button("reset"):
    st.session_state.state = state
    st.session_state.cur_idx = 0


def search():
    st.session_state.search_status = "searching..."
    st.session_state.search_results = []
    st.session_state.urls_to_scrape = []
    st.session_state.scraped_content = ["-"]

    st.session_state.search_status_container.write("searching...")
    st.session_state.state["current_query"] = st.session_state.query
    print("state", st.session_state.state)
    res = search2(
            st.session_state.state,
            writer=None,
            config={"configurable": {"max_search_results": 4}}
        )
    st.session_state.state_container.write("search completed")
    st.session_state.state["search_results"] = res["search_results"]

def get_best_urls():
    st.session_state.search_status_container.write("getting best urls...")
    res = get_best_urls_from_search(
        st.session_state.state,
        writer=None,
        config={"configurable": {"max_search_results": 4}}
    )
    st.session_state.state_container.write("urls retrieved")
    st.session_state.state["urls_to_scrape"] = res["urls_to_scrape"]

def scrape_urls_from_best_urls():
    st.session_state.search_status_container.write("retrieving urls...")
    res = scrape_urls(
        st.session_state.state,
        writer=None,
        config={"configurable": {"max_search_results": 4}}
    )
    st.session_state.state_container.write("scraped urls")
    st.session_state.state["scraped_content"] = res["scraped_content"]

left_col, right_col = st.columns([1,4])

def next_url():
    st.session_state.cur_idx += 1

def prev_url():
    st.session_state.cur_idx -= 1

with left_col:
    st.text_input("question", on_change=search, key="query")
    st.button("get best urls", on_click=get_best_urls)
    st.button("scrape urls", on_click=scrape_urls_from_best_urls)  
    st.write("STATUS")
    st.session_state.search_status_container = st.empty()
    prev_col, next_col = st.columns([1,1])    
    with prev_col:
        st.button("prev", on_click=prev_url)
    with next_col:
        st.button("next", on_click=next_url)


with right_col:
    st.write("state")
    st.session_state.state_container = st.empty()
    st.session_state.state_container.write(st.session_state.state)

    st.session_state.scraped_content_container = st.empty()
    container = st.container()
    if st.session_state.state["scraped_content"]:
        with container:
            st.write(f"idx: {st.session_state.cur_idx}")
            st.write(f"url: {st.session_state.state['urls_to_scrape'][st.session_state.cur_idx]}")
            st.markdown(st.session_state.state["scraped_content"][st.session_state.cur_idx])

st.markdown("---")
st.write("DEBUG")

