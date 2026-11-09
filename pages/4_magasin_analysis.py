import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

from utils.utils import Buttons, plot_stl, plot_spectrogram
from styling.colours import COLOURS

Buttons.home_button()
st.title("Magasin analysis")


# Retrieve reservoir data from NVE API
from utils.APIs.NVE_API import get_nve_data

df_nve = get_nve_data()

# Select area
areas = df_nve["area type"].unique().tolist()

selected_area = st.radio("Select area", areas, horizontal=True)

# Filter data by area
filtered_df = df_nve[df_nve["area type"] == selected_area]

tab1, tab2 = st.tabs(["STL decomposition", "Spectrogram"])

with tab1:
    st.subheader("STL decomposition")

    seasonal = st.number_input("Seasonal smoother", min_value=7, value=13, step=2)

    robust = st.checkbox("Robust decomposition", value=True)

    if st.button("Run STL"):
        fig = plot_stl(filtered_df, seasonal=seasonal, robust=robust)

        st.pyplot(fig)

with tab2:
    st.subheader("Spectrogram")

    window_length = st.number_input("Window length", min_value=2, value=365)

    overlap = st.number_input("Window overlap", min_value=0, value=300)

    if overlap >= window_length:
        st.error("Overlap must be smaller than window length.")

    elif st.button("Generate spectrogram"):
        fig = plot_spectrogram(
            filtered_df, window_length=window_length, overlap=overlap
        )

        st.pyplot(fig)
