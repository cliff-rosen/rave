import streamlit as st

st.title("App 2")
st.write("Hello, World!")
st.button("Reset")

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.status = "starting"
    st.session_state.count = 0
    st.session_state.f1_enabled = False

def set_f1_enabled(value):
    st.session_state.f1_enabled = value

st.checkbox("Enable 1", key="f1_enabled")

st.markdown("---")

if st.button("Update 1"):
    with st.session_state.container_1:
        st.write("C1")

st.markdown("---")

st.write("container_1: ")
if not st.session_state.f1_enabled:
    st.write("container 1 here:")
    st.session_state.container_1 = st.empty()

st.markdown("---")

st.write("container_2: ")
st.write("container 2 here:")
st.session_state.container_2 = st.empty()

st.markdown("---")

if st.button("Update 2"):
    st.write("clicked here")
    with st.session_state.container_2:
        st.write("C2")

st.markdown("---")

st.write("OUTPUT")
if st.session_state.initialized:
    st.write("Status: ", st.session_state.status)
    st.write("Count: ", st.session_state.count)
    st.write("f1_enabled: ", st.session_state.f1_enabled)
