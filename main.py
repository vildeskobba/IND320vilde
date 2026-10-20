import streamlit as st

st.set_page_config(page_title="My App", layout="wide", initial_sidebar_state="expanded")

pages = [
    st.Page("pages/home.py", title="Home", icon=":material/home:"),
    st.Page("pages/imported_data.py", title="Imported data", icon=":material/table:"),
    st.Page("pages/plot.py", title="Plot", icon=":material/analytics:"),
    st.Page("pages/power_flows.py", title="Power flows", icon=":material/info:"),
]

pg = st.navigation(pages, position="sidebar")

pg.run()


# streamlit run main.py
