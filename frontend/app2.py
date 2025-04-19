import streamlit as st
import time

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.status_messages = []
    st.session_state.state = 0
    st.session_state.x = 0
    st.session_state.message = "hello"
    st.session_state.message_container = None
    st.session_state.message_container_2 = None

st.button("refresh")


def increment_x():
    st.session_state.x += 1

if st.button("increment x"):
    increment_x()

some_text = st.text_input("some text", on_change=increment_x)


st.write("x: ", st.session_state.x)
st.write("some text: ", some_text)
