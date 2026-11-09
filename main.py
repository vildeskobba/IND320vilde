import streamlit as st

st.set_page_config(page_title="My App", layout="wide", initial_sidebar_state="expanded")

pages = [
    st.Page("pages/0_home.py", title="Home", icon=":material/home:"),
    st.Page("pages/1_imported_data.py", title="Imported data", icon=":material/table:"),
    st.Page("pages/2_plot.py", title="Plot", icon=":material/analytics:"),
    st.Page("pages/3_power_flows.py", title="Power flows", icon=":material/bolt:"),
    st.Page(
        "pages/4_magasin_analysis.py",
        title="Magasin analysis",
        icon=":material/south_america:",
    ),
    st.Page(
        "pages/5_meteorological_analysis.py",
        title="Meteorological analysis",
        icon=":material/cloud:",
    ),
]

pg = st.navigation(pages, position="sidebar")

pg.run()


# streamlit run main.py
