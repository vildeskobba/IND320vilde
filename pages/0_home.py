import streamlit as st
from styling import style_funcs
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pymongo import MongoClient
import certifi
import branca.colormap as cm
from utils.utils import Buttons
from styling.colours import COLOURS

st.title("Welcome")
st.write(
    "This is the home page. You can choose a page from the menu bellow. If you want, you can use the sidebar menu to navigate pages."
)
st.write("On other pages, you can always press the house to get back to this page.")


st.title("Map")


# Load GeoJSON files and convert to latitude/longitude
budomrader = gpd.read_file("data/nve/geoJSON/Budomrader.geojson").to_crs(epsg=4326)

# Create map
m = folium.Map(
    location=[
        budomrader.geometry.centroid.y.mean(),
        budomrader.geometry.centroid.x.mean(),
    ],
    zoom_start=4,
    zoom_control=False,
    scrollWheelZoom=False,
    dragging=False,
    doubleClickZoom=False,
    touchZoom=False,
    boxZoom=False,
)
bounds = budomrader.total_bounds

m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=(-50, -50))


# Get previously selected area
map_selected_area = st.session_state.get("map_selected_area")
if "selected_area" not in st.session_state:
    st.session_state["selected_area"] = None


def style_function(feature):
    area = feature["properties"]["budomr"]

    is_selected = area == map_selected_area

    return {
        "color": COLOURS["ALMOST_BLACK_PINK"] if is_selected else COLOURS["PINK"],
        "weight": 4 if is_selected else 1,
        "fillOpacity": 0.2,
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


map_data = st_folium(
    m,
    width=700,
    height=800,
    key="area_selection_map",
    returned_objects=["last_active_drawing"],
)

# Detect clicked area
if map_data and map_data["last_active_drawing"]:
    clicked_area = map_data["last_active_drawing"]["properties"]["budomr"]

    if clicked_area != st.session_state.get("map_selected_area"):
        st.session_state["map_selected_area"] = clicked_area
        st.rerun()


if st.button("Plot"):
    st.switch_page("pages/2_plot.py")

if st.button("Power flows"):
    st.switch_page("pages/3_power_flows.py")

if st.button("Magasin analysis"):
    st.switch_page("pages/4_magasin_analysis.py")
if st.button("Forecast"):
    st.switch_page("pages/7_forecast.py")
if st.button("Meteorological analysis"):
    st.switch_page("pages/5_meteorological_analysis.py")


if st.button("Imported data"):
    st.switch_page("pages/9_imported_data.py")

style_funcs.style_home_menu_button()
