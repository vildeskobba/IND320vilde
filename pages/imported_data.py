import streamlit as st
import pandas as pd

from utils import Buttons
from styling.colours import COLOURS

Buttons.home_button()
st.title("Imported data")

from utils import load_data

df = load_data("reservoirs.csv")


def display_data_table(df):
    df["date"] = pd.to_datetime(df["date"])

    last_month = df["date"].max() - pd.DateOffset(months=1)

    last_month_df = df[
        (df["date"] > last_month) &
        (df["date"] <= df["date"].max())
    ]

    rows = []

    for column in [
        "reservoir level",
        "capacity (TWh)",
        "level (TWh)",
        "reservoir level last week",
        "change level"
    ]:
        rows.append({
            "Column": column,
            "Data": last_month_df[column].tolist()
        })

    table_df = pd.DataFrame(rows)

    st.dataframe(
        table_df,
        column_config={
            "Data": st.column_config.LineChartColumn(
                "Last month", 
                color=COLOURS["PINK"]
            )
        },
        hide_index=True,
        use_container_width=True
    )

display_data_table(df)

df