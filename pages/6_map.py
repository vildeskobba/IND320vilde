import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pymongo import MongoClient
import certifi
import branca.colormap as cm
from utils.utils import Buttons, plot_precipitation_outliers, plot_temperature_anomalies
from styling.colours import COLOURS

Buttons.home_button()
st.title("Map")


# Connect to MongoDB
@st.cache_resource
def get_client():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())


client = get_client()
db = client["power_data"]

# Load weekly averages from MongoDB
magasin_df = pd.DataFrame(list(db["weekly_averages_magasin"].find({}, {"_id": 0})))

power_flows_df = pd.DataFrame(
    list(db["weekly_averages_net_power_flows"].find({}, {"_id": 0}))
)

weather_df = pd.DataFrame(list(db["weekly_averages_weather"].find({}, {"_id": 0})))

# Load GeoJSON files and convert to latitude/longitude
budomrader = gpd.read_file("data/nve/geoJSON/Budomrader.geojson").to_crs(epsg=4326)

# Select what to color by and available time periods
color_by = st.segmented_control(
    "Color by:",
    options=["Percipation", "Temperature", "Power flow", "Reservoir level"],
    default="Temperature",
    selection_mode="single",
)

df = pd.DataFrame()
if color_by == "Percipation":
    df = weather_df[["area", "iso_year", "iso_week", "precipitation"]]
elif color_by == "Temperature":
    df = weather_df[["area", "iso_year", "iso_week", "temperature"]]
elif color_by == "Power flow":
    df = power_flows_df
else:
    df = magasin_df

df["area"] = df["area"].str.replace("_", " ", regex=False)


# Select year and week
all_periods = df[["iso_year", "iso_week"]].drop_duplicates()

years = sorted(all_periods["iso_year"].unique())

selected_year = st.selectbox("Year", years, index=len(years) - 1)

weeks = sorted(
    all_periods.loc[all_periods["iso_year"] == selected_year, "iso_week"].unique()
)

selected_week = st.selectbox("Week", weeks, index=len(weeks) - 1)

df_numerical_col_name = {
    "weather_df_perc": "precipitation",
    "weather_df_temp": "temperature",
    "power_flows_df": "net_exported",
    "magasin_df": "reservoir_level",
}

# Create map
m = folium.Map(
    location=[
        budomrader.geometry.centroid.y.mean(),
        budomrader.geometry.centroid.x.mean(),
    ],
    zoom_start=4,
)
bounds = budomrader.total_bounds

m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=(-50, -50))


# This is the numerical columns for the dfs
numerical_col = {
    "Percipation": "precipitation",
    "Temperature": "temperature",
    "Power flow": "net_exported",
    "Reservoir level": "reservoir_level",
}[color_by]

df["iso_year"] = pd.to_numeric(df["iso_year"], errors="coerce")
df["iso_week"] = pd.to_numeric(df["iso_week"], errors="coerce")
df[numerical_col] = pd.to_numeric(df[numerical_col], errors="coerce")

# Filter selected year and week
df_selected = df[(df["iso_year"] == selected_year) & (df["iso_week"] == selected_week)][
    ["area", numerical_col]
]

# Calculate global maximum (all years and weeks)
vmax = df[numerical_col].max()
vmin = df[numerical_col].min()

# Create color scale
colormap = cm.LinearColormap(
    colors=["violet", "blue", "cyan", "lime", "yellow", "orange", "red"],
    vmin=vmin,
    vmax=vmax,
    caption=f"{numerical_col} (vmin - {vmax:.2f})",
)

# Create dictionary: area -> value
values = df_selected.set_index("area")[numerical_col].to_dict()


# Style each geographical area
def style_function(feature):
    area = feature["properties"]["budomr"]
    value = values.get(area)

    return {
        "fillColor": colormap(value) if pd.notna(value) else "white",
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.7,
    }


# Add GeoJSON layer
folium.GeoJson(
    budomrader,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["budomr"],
        aliases=["Area:"],
    ),
).add_to(m)

# Add legend
colormap.add_to(m)

st_folium(m, width=700, height=800)
