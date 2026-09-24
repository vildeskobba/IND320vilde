import streamlit as st
from styling import style_funcs

st.title("Welcome")
st.write("This is the home page. You can choose a page from the menu bellow. If you want, you can use the sidebar menu to navigate pages.")
st.write("On other pages, you can always press the house to get back to this page.")


if st.button("Imported data"):
    st.switch_page("pages/imported_data.py")

if st.button("Plot"):
    st.switch_page("pages/plot.py")

if st.button("Page 4"):
    st.switch_page("pages/page_4.py")


style_funcs.style_home_menu_button()