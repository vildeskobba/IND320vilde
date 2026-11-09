import streamlit as st
from styling import style_funcs

st.title("Welcome")
st.write(
    "This is the home page. You can choose a page from the menu bellow. If you want, you can use the sidebar menu to navigate pages."
)
st.write("On other pages, you can always press the house to get back to this page.")


if st.button("Imported data"):
    st.switch_page("pages/1_imported_data.py")

if st.button("Plot"):
    st.switch_page("pages/2_plot.py")

if st.button("Power flows"):
    st.switch_page("pages/3_power_flows.py")

if st.button("Magasin analysis"):
    st.switch_page("pages/4_magasin_analysis.py")

if st.button("Meteorological analysis"):
    st.switch_page("pages/5_meteorological_analysis.py")

style_funcs.style_home_menu_button()
