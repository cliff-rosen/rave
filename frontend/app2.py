import streamlit as st
import time

# Page configuration
st.set_page_config(
    page_title="RAVE - Recursive Agent for Verified Explanations",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)


# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.container_1 = None

col1, col2 = st.columns(2)

with col1:
    st.write("Hello")
    if "container_1" not in st.session_state:
        st.session_state.container_1 = st.empty()
    
    if st.button("Click me"):
        st.write("Clicked")

with col2:
    st.write("World")
    if st.button("Click me 2"):
        st.write("Clicked 2")
        time.sleep(1)
        st.write("1")
        time.sleep(1)
        st.write("2")
        time.sleep(1)
        st.write("3")
        time.sleep(1)
        st.write("4")
        time.sleep(1)

if st.button("Click me 3"):
    st.write("Clicked 3")
    with st.session_state.container_1:
        st.write("Hello")
        time.sleep(1)
        st.write("1")
        time.sleep(1)
        st.write("2")
        time.sleep(1)
