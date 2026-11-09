import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

from utils.utils import Buttons, plot_precipitation_outliers, plot_temperature_anomalies
from styling.colours import COLOURS

Buttons.home_button()
st.title("Meteorological analysis")

# Load shapefile
budomrader = gpd.read_file("data_nve/Budområder/Budområder.shp")
# Convert to latitude/longitude
budomrader = budomrader.to_crs(epsg=4326)

# load weather data
weather_data = pd.read_parquet("data_weather/weather_data.parquet")


# Area selection
areas = sorted(budomrader["budomr"].dropna().unique().tolist())
selected_areas = st.pills("Select delivery areas", areas, selection_mode="multi")
""""""

if selected_areas:
    # Convert weather data to GeoDataFrame
    weather_gdf = gpd.GeoDataFrame(
        weather_data,
        geometry=gpd.points_from_xy(
            weather_data["longitude"],
            weather_data["latitude"],
        ),
        crs="EPSG:4326",
    )

    # Filter selected delivery areas
    selected_polygons = budomrader[budomrader["budomr"].isin(selected_areas)]

    # Spatial join
    weather_gdf = gpd.sjoin(
        weather_gdf,
        selected_polygons,
        how="inner",
        predicate="within",
    )

    # Convert back to DataFrame
    weather_data = pd.DataFrame(weather_gdf.drop(columns=["geometry", "index_right"]))
st.write(f"Number of weather observations: {len(weather_data)}")
""""""


def map_style_function(feature):
    area = feature["properties"]["budomr"]
    if area in (selected_areas or []):
        return {
            "fillColor": COLOURS["PINK"],
            "color": COLOURS["ALMOST_BLACK_PINK"],
            "weight": 1,
            "fillOpacity": 0.8,
        }
    return {
        "fillColor": COLOURS["ALMOST_WHITE_PINK"],
        "color": COLOURS["ALMOST_BLACK_PINK"],
        "weight": 1,
        "fillOpacity": 0.2,
    }


# Create map
m = folium.Map(
    location=[
        budomrader.geometry.centroid.y.mean() + 2,
        budomrader.geometry.centroid.x.mean() + 5,
    ],
    zoom_start=2.5,
)
folium.GeoJson(
    budomrader,
    style_function=map_style_function,
).add_to(m)
st_folium(m, width=150, height=300)
# Add shapefile
folium.GeoJson(budomrader).add_to(m)

tab1, tab2 = st.tabs(["Outlier / SPC", "Anomaly / LOF"])

with tab1:
    st.subheader("Precipitation outlier detection")

    cutoff = st.slider("DCT frequency cutoff", min_value=1, max_value=200, value=15)

    n_std = st.slider(
        "Number of standard deviations",
        min_value=1.0,
        max_value=5.0,
        value=2.0,
        step=0.5,
    )

    if st.button("Run precipitation analysis"):
        fig, outliers = plot_precipitation_outliers(
            weather_data, cutoff=cutoff, n_std=n_std
        )

        st.pyplot(fig)

        st.subheader("Outlier statistics")
        st.metric("Number of outliers", len(outliers))

        st.dataframe(outliers)

        if not outliers.empty:
            st.download_button(
                "Download outlier data",
                outliers.to_csv(index=False),
                file_name="precipitation_outliers.csv",
                mime="text/csv",
            )

with tab2:
    st.subheader("Temperature anomaly detection")

    contamination = st.slider(
        "Expected proportion of anomalies",
        min_value=0.001,
        max_value=0.10,
        value=0.01,
        step=0.001,
        format="%.3f",
    )

    n_neighbors = st.slider(
        "Number of neighbours", min_value=5, max_value=100, value=20
    )

    if st.button("Run temperature analysis"):
        fig, anomalies = plot_temperature_anomalies(
            weather_data, contamination=contamination, n_neighbors=n_neighbors
        )

        st.pyplot(fig)

        st.subheader("Anomaly statistics")

        st.metric("Number of anomalies", len(anomalies))

        st.dataframe(anomalies)

        if not anomalies.empty:
            st.download_button(
                "Download anomaly data",
                anomalies.to_csv(index=False),
                file_name="temperature_anomalies.csv",
                mime="text/csv",
            )
