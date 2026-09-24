import streamlit as st
from .colours import COLOURS


def style_home_button():
    st.markdown(f"""
    <style>
    div.stButton > button {{
        background-color: {COLOURS['LIGHT_PINK']};
        color: white;
        border: none;
    }}

    div.stButton > button:hover {{
        background-color: {COLOURS['PINK']};
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

def style_selectbox():
    #style the select box
    st.markdown(f"""
    <style>
    div[data-baseweb="select"] > div {{
        background-color: {COLOURS["ALMOST_WHITE_PINK"]};
        color: {COLOURS["ALMOST_BLACK_PINK"]};
    }}

    div[data-baseweb="select"] svg {{
        fill: white;
    }}
    </style>
    """, unsafe_allow_html=True)

def style_slider():
    st.markdown(f"""
    <style>
    /* Select slider */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="progressbar"] {{
        background-color: {COLOURS["PINK"]} !important;
    }}

    /* Slider handles */
    div[data-testid="stSlider"] div[role="slider"] {{
        background-color: {COLOURS["PINK"]} !important;
        border-color: {COLOURS["PINK"]} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def style_home_menu_button(): 
    st.markdown(f"""
    <style>
    div.stButton > button {{
        width: 400px;
        height: 100px;
        margin: 15px auto;
        display: block;
        border-radius: 15px;
        background-color: {COLOURS['LIGHT_PINK']};
        color: {COLOURS['ALMOST_WHITE_PINK']};
        border: none;
    }}

    div.stButton > button p {{
        font-size: 32px !important;
        font-weight: bold !important;
        color: {COLOURS['ALMOST_WHITE_PINK']} !important;
    }}

    div.stButton > button:hover {{
        background-color: {COLOURS['PINK']};
        color: {COLOURS['ALMOST_WHITE_PINK']};
    }}
    </style>
    """, unsafe_allow_html=True)

