import streamlit as st
import pandas as pd

from utils import Buttons
from styling.colours import COLOURS

Buttons.home_button()
st.title("Imported data")

from NVE_API import get_nve_data

# this function uses the api to fetch data
df = get_nve_data()


def display_data_table(df):
    df["date"] = pd.to_datetime(df["date"])

    last_month = df["date"].max() - pd.DateOffset(months=1)

    last_month_df = df[(df["date"] > last_month) & (df["date"] <= df["date"].max())]

    rows = []

    for column in [
        "reservoir level",
        "capacity (TWh)",
        "level (TWh)",
        "reservoir level last week",
        "change level",
    ]:
        rows.append({"Column": column, "Data": last_month_df[column].tolist()})

    table_df = pd.DataFrame(rows)

    st.dataframe(
        table_df,
        column_config={
            "Data": st.column_config.LineChartColumn(
                "Last month", color=COLOURS["PINK"]
            )
        },
        hide_index=True,
        use_container_width=True,
    )


# Select area
areas = df["area type"].unique().tolist()

selected_area = st.radio("Select area", areas, horizontal=True)

# Filter data
filtered_df = df[df["area type"] == selected_area]

# Display table and plots
display_data_table(filtered_df)
