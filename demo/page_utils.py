import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def login():
    """
    Create a login form and handle simple user authentication.
    """
    for _ in range(5):
        st.write("")

    col1, _ = st.columns([1, 1.5])
    with col1:
        with st.form("login_form"):
            st.header("Log in")
            st.write("")
            username = st.text_input("User ID")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                # Modify id & pw before deploying
                correct_username = "admin"  # os.getenv("STREAMLIT_ID")
                correct_password = "admin"  # os.getenv("STREAMLIT_PW")
                if username == correct_username and password == correct_password:
                    st.success("Login successful!")
                    st.session_state["login"] = True
                    st.rerun()
                else:
                    st.error("Incorrect username or password")


def logout():
    """
    Handle user logout by clearing session state and rerunning the app.
    """
    st.session_state["login"] = None
    st.rerun()
