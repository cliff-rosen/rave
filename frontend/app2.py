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

if st.session_state.x == 0:
    st.write("button 0")

if st.session_state.x == 1:
    st.write("button 1")

st.session_state.message_container = st.empty()
with st.session_state.message_container:
    st.write("message: ", st.session_state.message)

def agent_loop():
    st.session_state.message = "agent loop 1"
    for i in range(2):
        print("agent loop", i)
        st.session_state.message_container.write("agent loop" + str(i))
        time.sleep(1)
    st.session_state.message = "agent loop 2"
    st.session_state.x = 1

if st.button("agent loop"):
    agent_loop()

st.write("message 2: ", st.session_state.message)
