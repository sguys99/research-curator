import streamlit as st
from dotenv import load_dotenv
from page_utils import login, logout
from PIL import Image

load_dotenv()

if "login" not in st.session_state:
    st.session_state["login"] = False


st.set_page_config(
    page_title="flex ML Project Service Demo page",
    page_icon=Image.open("../img/logo-circle.png"),
    layout="wide",
)

st.write("<style>div.row-widget.stRadio > div{flex-direction:row;}</style>", unsafe_allow_html=True)

login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

home = st.Page(
    "home/home.py",
    title="Home page",
    icon=":material/home:",
    default=True,
)


app1_1 = st.Page(
    "app1/app1-1.py",
    title="App 1-1",
    icon=":material/smart_toy:",
)

app1_2 = st.Page(
    "app1/app1-2.py",
    title="App 1-2",
    icon=":material/smart_toy:",
)

app2_1 = st.Page(
    "app2/app2-1.py",
    title="App 2-1",
    icon=":material/monitoring:",
)

app2_2 = st.Page(
    "app2/app2-2.py",
    title="App 2-2",
    icon=":material/monitoring:",
)


if st.session_state["login"]:
    pg = st.navigation(
        {
            "⚙️ Logout": [logout_page],
            "0️⃣ Home": [home],
            "1️⃣ Application1": [app1_1, app1_2],
            "2️⃣ Application2": [app2_1, app2_2],
        },
    )
else:
    pg = st.navigation([login_page])


with st.sidebar:
    st.image("../img/logo.png", width=200)

pg.run()
