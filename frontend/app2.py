import streamlit as st

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.status_messages = []

def output_values_for_selected_status(idx):
    print("output_values_for_selected_status", idx)

def output_status_messages():
    print("output_status_messages", st.session_state.status_messages)
    # Display status messages in a table format
    if not st.session_state.status_messages:
        return

    with st.session_state.status_area:
        st.empty()
        message_container = st.container()
        with message_container:
                for msg in st.session_state.status_messages:
                    st.button(
                        label=msg["message"],                          # what the user sees
                        key=f"msg_{msg['update_idx']}.{msg['message']}",                # add unique key
                        on_click=output_values_for_selected_status,
                        args=(msg["update_idx"],)                      # tuple of positional args
                    )

def update_status_messages(message_text):
    update_idx = len(st.session_state.status_messages) - 1
    message = {"update_idx": update_idx, "message": message_text}
    st.session_state.status_messages.append(message)
    # output_status_messages()

st.write("Hello")

st.button("Add Status Message", on_click=update_status_messages, args=("New Status Message [1]",))

st.session_state.status_area = st.empty()
output_status_messages()

# if st.session_state.status_messages:
#     for msg in st.session_state.status_messages:
#         st.button(
#             label=msg["message"],                          # what the user sees
#             key=f"msg_{msg['update_idx']}.{msg['message']}",                # add unique key
#             on_click=output_values_for_selected_status,
#             args=(msg["update_idx"],)                      # tuple of positional args
#         )


