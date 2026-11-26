import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pymongo import MongoClient
import certifi

from utils.utils import Buttons
from styling.colours import COLOURS

Buttons.home_button()

st.title("Power flows")


# Connect to MongoDB
@st.cache_resource
def get_client():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())


client = get_client()
db = client["power_data"]


# Columns with specified width
left, right = st.columns([2, 3])


# --------------------------------------------------
# LEFT SIDE: PIE CHART
# --------------------------------------------------

with left:
    annual_collection = db["annual_flows"]
    annual_df = pd.DataFrame(list(annual_collection.find({}, {"_id": 0})))

    st.subheader("Flow distribution 2025")

    # Function to show pie chart for selected border
    def show_pie_for_selected_border(zone_a, zone_b):

        pie_df = (
            annual_df[
                ((annual_df["from_zone"] == zone_a) & (annual_df["to_zone"] == zone_b))
                | (
                    (annual_df["from_zone"] == zone_b)
                    & (annual_df["to_zone"] == zone_a)
                )
            ]
            .groupby(["from_zone", "to_zone"], as_index=False)["total_mw"]
            .sum()
        )

        if not pie_df.empty:
            pie_df["direction"] = pie_df["from_zone"] + " → " + pie_df["to_zone"]

            fig = px.pie(
                pie_df,
                values="total_mw",
                names="direction",
                title=f"Power Flow Between {zone_a} and {zone_b}",
                color_discrete_sequence=[
                    COLOURS["PINK"],
                    COLOURS["DARK_PINK"],
                ],
            )

            fig.update_traces(
                textposition="inside",
                textinfo="label+percent",
                textfont=dict(
                    color=COLOURS["ALMOST_WHITE_PINK"],
                    size=13,
                    family="Arial",
                ),
                hovertemplate=(
                    "%{label}<br>"
                    "Flow: %{value:,.0f} MW<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                height=450,
                margin=dict(t=60, b=20, l=20, r=20),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning(f"No flow data found for {zone_a} and {zone_b}.")

    # Radio buttons to select border
    border_data = {
        ("NO_1", "SE_3"): None,
        ("NO_2", "DK_1"): None,
        ("NO_2", "NL"): None,
        ("NO_2", "DE_LU"): None,
        ("NO_2", "GB"): None,
        ("NO_3", "SE_2"): None,
        ("NO_4", "SE_2"): None,
    }

    selected_border = st.radio(
        "Select border",
        options=list(border_data.keys()),
        format_func=lambda border: f"{border[0]} ↔ {border[1]}",
    )

    show_pie_for_selected_border(*selected_border)


# --------------------------------------------------
# RIGHT SIDE: LINE CHART
# --------------------------------------------------

with right:
    # Get data from database
    collection = db["daily_average_flows"]
    data = list(collection.find({}, {"_id": 0}))

    pdf = pd.DataFrame(data)
    pdf["timestamp"] = pd.to_datetime(pdf["timestamp"])

    # Available selections, months and years
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    years = sorted(pdf["timestamp"].dt.year.unique(), reverse=True)

    # Select year
    selected_year = st.selectbox(
        "Select year",
        years,
        key="flow_year",
    )

    # Available months
    available_months = set(
        pdf.loc[
            pdf["timestamp"].dt.year == selected_year,
            "timestamp",
        ].dt.month.unique()
    )

    # Add "no data" to unavailable months
    month_labels = [
        month if i + 1 in available_months else f"{month} (no data)"
        for i, month in enumerate(month_names)
    ]

    # Month selection
    selected_month = st.pills(
        "Select month",
        options=month_labels,
        default=next(
            (month_labels[i] for i in range(12) if i + 1 in available_months),
            None,
        ),
        selection_mode="single",
        key="flow_month",
    )

    # Filter data for selected year and month
    if selected_month and "(no data)" not in selected_month:
        month_number = month_names.index(selected_month)

        filtered_pdf = pdf[
            (pdf["timestamp"].dt.month == month_number + 1)
            & (pdf["timestamp"].dt.year == selected_year)
        ]

        if not filtered_pdf.empty:
            # Sort data
            filtered_pdf = filtered_pdf.sort_values("timestamp")

            # Create interactive line chart
            fig = px.line(
                filtered_pdf,
                x="timestamp",
                y="flow_mw",
                color="from_zone",
                line_dash="to_zone",
                markers=True,
                title=f"Average Power Flows — {selected_month} {selected_year}",
                labels={
                    "timestamp": "Date",
                    "flow_mw": "Average power flow (MW)",
                    "from_zone": "From zone",
                    "to_zone": "To zone",
                },
            )

            # Configure hover information
            fig.update_traces(
                hovertemplate=(
                    "Date: %{x|%Y-%m-%d}<br>Power flow: %{y:,.0f} MW<extra></extra>"
                ),
                marker=dict(size=5),
            )

            # Configure layout
            start = pd.Timestamp(selected_year, month_number + 1, 1)
            end = start + pd.offsets.MonthBegin(1)

            fig.update_layout(
                xaxis=dict(
                    title="Date",
                    range=[start, end],
                ),
                yaxis_title="Average power flow (MW)",
                hovermode="x unified",
                height=550,
                legend_title="Power flow",
                margin=dict(t=60, b=40, l=40, r=20),
            )

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Select a month with available data.")


# --------------------------------------------------
# DATA SOURCE
# --------------------------------------------------

with st.expander("Data source"):
    st.write(
        "The data comes from the MongoDB database `power_data`.\n\n"
        "- **Flow distribution (pie chart):** Collection `annual_flows`, "
        "containing annual aggregated power flows between zones for 2025.\n\n"
        "- **Average power flows (line chart):** Collection "
        "`daily_average_flows`, containing daily average power flows "
        "between zones, with timestamps used to filter by year and month."
    )
