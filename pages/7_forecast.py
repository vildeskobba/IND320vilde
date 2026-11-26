import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pymongo import MongoClient
import certifi
import branca.colormap as cm
from utils.utils import Buttons, forecast_reservoir, evaluate_forecast
from styling.colours import COLOURS

Buttons.home_button()
st.title("Forecast for reservoir levels")
Buttons.use_map_selected_area_button()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from datetime import date, timedelta
from statsmodels.tsa.stattools import acf


# Connect to MongoDB
@st.cache_resource
def get_client():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())


client = get_client()
db = client["power_data"]

magasin_df = pd.DataFrame(list(db[f"weekly_averages_magasin"].find({}, {"_id": 0})))
entso_df = pd.DataFrame(list(db[f"weekly_averages_power_flows"].find({}, {"_id": 0})))
weather_df = pd.DataFrame(list(db[f"weekly_averages_weather"].find({}, {"_id": 0})))
exchange_df = pd.DataFrame(
    list(db[f"weekly_averages_exchange_rates"].find({}, {"_id": 0}))
)
# Load GeoJSON files and convert to latitude/longitude
budomrader = gpd.read_file("data/nve/geoJSON/Budomrader.geojson").to_crs(epsg=4326)


areas = sorted(budomrader["budomr"].dropna().unique().tolist())

st.subheader("Select data sources")


data_sources_dict = {
    "Power flows (ENTSO)": "entso",
    "Weather": "weather",
    "Exchange rates": "exchange",
}

selected_data_sources = tuple(
    value for name, value in data_sources_dict.items() if st.checkbox(name)
)

if (
    st.session_state.get("use_map_selected_area", False)
    and st.session_state.get("map_selected_area") is not None
):
    selected_area = st.session_state["map_selected_area"]
else:
    selected_area = st.pills(
        "Select forecast area",
        areas,
        default="NO 1",
        selection_mode="single",
    )
if selected_area:
    selected_area = selected_area.replace(" ", "_")
else:
    st.write("Please select an area or use the map selected one from home page. ")
if selected_area is not None:
    st.subheader("Model parameters")

    model_type = st.segmented_control(
        "Model type:",
        options=["SARIMAX", "RIVER"],
        default="SARIMAX",
        selection_mode="single",
    )
    if model_type == "RIVER":
        st.subheader("RIVER parameters")
        l2 = st.number_input("L2 regularization", 0.0, 1.0, 0.01)
        model_params = {"l2": l2}
    else:
        st.subheader("SARIMAX parameters")

        p = st.number_input("AR (p)", 0, 5, 1)
        d = st.number_input("Differencing (d)", 0, 2, 1)
        q = st.number_input("MA (q)", 0, 5, 1)

        P = st.number_input("Seasonal AR (P)", 0, 3, 0)
        D = st.number_input("Seasonal differencing (D)", 0, 2, 0)
        Q = st.number_input("Seasonal MA (Q)", 0, 3, 0)
        s = st.number_input("Seasonal period (s)", 0, 52, 0)

        model_params = {"order": (p, d, q), "seasonal_order": (P, D, Q, s)}

    history_weeks = st.slider(
        "History (weeks)", min_value=50, max_value=200, value=150, step=1
    )

    horizon_weeks = st.segmented_control(
        "Horizon (weeks):",
        options=[2, 4, 6, 8],
        default=4,
        selection_mode="single",
    )
    """"""
    start_date = st.date_input(
        "Training start date", value=date.today() - timedelta(weeks=150)
    )

    end_date = st.date_input("Training end date", value=date.today())

    start_iso = start_date.isocalendar()
    end_iso = end_date.isocalendar()

    start_iso_week = start_iso.week
    start_iso_year = start_iso.year

    end_iso_week = end_iso.week
    end_iso_year = end_iso.year

    def filter_by_iso_date(df, start_year, start_week, end_year, end_week):

        start = start_year * 100 + start_week
        end = end_year * 100 + end_week

        iso_dates = df["iso_year"] * 100 + df["iso_week"]

        return df[(iso_dates >= start) & (iso_dates <= end)].copy()

    magasin_filtered = filter_by_iso_date(
        magasin_df, start_iso_year, start_iso_week, end_iso_year, end_iso_week
    )

    entso_filtered = filter_by_iso_date(
        entso_df, start_iso_year, start_iso_week, end_iso_year, end_iso_week
    )

    weather_filtered = filter_by_iso_date(
        weather_df, start_iso_year, start_iso_week, end_iso_year, end_iso_week
    )

    exchange_filtered = filter_by_iso_date(
        exchange_df, start_iso_year, start_iso_week, end_iso_year, end_iso_week
    )

    """"""

    if selected_area and model_type and horizon_weeks:
        col1, col2 = st.columns(2)

        with col1:
            evaluate_button = st.button("Evaluate model", use_container_width=True)

        with col2:
            forecast_button = st.button("Get forecast", use_container_width=True)

        if forecast_button:
            forecast = forecast_reservoir(
                magasin_df=magasin_filtered,
                entso_df=entso_filtered,
                weather_df=weather_filtered,
                exchange_df=exchange_filtered,
                area=selected_area,
                model_type=model_type,
                history_weeks=history_weeks,
                horizon_weeks=horizon_weeks,
                data_sources=selected_data_sources,
                target="reservoir_level",
                model_params=model_params,
            )
            st.dataframe(forecast)

        elif evaluate_button:
            score = evaluate_forecast(
                magasin_df=magasin_filtered,
                entso_df=entso_filtered,
                weather_df=weather_filtered,
                exchange_df=exchange_filtered,
                area=selected_area,
                model_type=model_type,
                history_weeks=history_weeks,
                horizon_weeks=horizon_weeks,
                data_sources=selected_data_sources,
                target="reservoir_level",
                model_params=model_params,
            )
            st.write(f"MAE: {score['MAE'].mean():.4f}")
            st.write(f"RSME: {score['RMSE'].mean():.4f}")

        else:
            st.write("Press a button :)")

else:
    st.write("Please select an area or use the map selected one from home page. ")
