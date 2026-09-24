import streamlit as st
import pandas as pd
from pathlib import Path

from styling import style_funcs

class Buttons:
    @staticmethod
    def home_button():
        if st.button("", icon=":material/home:"):
            st.switch_page("pages/home.py")
        style_funcs.style_home_button()


@st.cache_data
def load_data(file_name):
    file_path = Path(__file__).parent / file_name
    reservoirs_df = pd.read_csv(file_path)
    reservoirs_df.columns = [
    'date',
    'area type',
    'area number',
    'year (ISO)',
    'week (ISO)',
    'reservoir level',
    'capacity (TWh)',
    'level (TWh)',
    'next publishing date',
    'reservoir level last week',
    'change level'
    ] 
    return reservoirs_df

