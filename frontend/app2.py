import streamlit as st
import time


st.write("before")

x = st.empty()
if "y" not in st.session_state:
    st.session_state.y = st.empty()
z = st.empty()

st.write("after")

with x:
    st.write("x")

with st.session_state.y:
    st.write("y")

with z:
    st.write("z")

if st.button("here"):
    st.write("clicked")

if st.button("here y"):
    with st.session_state.y:
        st.write("y2")

if st.button("here z"):
    with z:
        st.write("z2")



