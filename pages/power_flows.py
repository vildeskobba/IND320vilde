import streamlit as st
from utils import Buttons
from styling.colours import COLOURS

Buttons.home_button()

import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
import certifi

st.title("Power flows")


# Connect to MongoDB
@st.cache_resource
def get_client():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())


client = get_client()
db = client["power_data"]

# columns with specified width
left, right = st.columns([2, 3])

# left side: pie chart
with left:
    annual_collection = db["annual_flows"]
    annual_df = pd.DataFrame(list(annual_collection.find({}, {"_id": 0})))

    st.subheader("Flow distribution 2025")

    # function to show pie chart for specified border
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
            fig, ax = plt.subplots()

            wedges, texts, autotexts = ax.pie(
                pie_df["total_mw"],
                labels=pie_df["from_zone"] + " → " + pie_df["to_zone"],
                autopct="%1.1f%%",
                startangle=90,
                colors=[
                    COLOURS["PINK"],
                    COLOURS["DARK_PINK"],
                ],
                textprops={"color": COLOURS["ALMOST_WHITE_PINK"], "fontweight": "bold"},
            )
            for text in texts:
                text.set_color(COLOURS["ALMOST_BLACK_PINK"])

            for text in autotexts:
                text.set_color(COLOURS["ALMOST_WHITE_PINK"])
                text.set_fontweight("bold")
                text.set_fontsize(13)

            ax.set_title(f"Power Flow Between {zone_a} and {zone_b}")
            st.pyplot(fig)
            plt.close(fig)

        else:
            st.warning(f"No flow data found for {zone_a} and {zone_b}.")

    # radio buttons to select border
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

# right side: line chart
with right:
    # get data from the database and make it into a pandas df
    collection = db["daily_average_flows"]
    data = list(collection.find({}, {"_id": 0}))
    pdf = pd.DataFrame(data)
    pdf["timestamp"] = pd.to_datetime(pdf["timestamp"])

    # available selections, months and years
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

    # select box to choose year
    selected_year = st.selectbox("Select year", years, key="flow_year")

    # pill buttons for selecting months :
    available_months = set(
        pdf.loc[
            pdf["timestamp"].dt.year == selected_year, "timestamp"
        ].dt.month.unique()
    )

    # adding "no data" to the buttons that points to months without data
    month_labels = [
        month if i + 1 in available_months else f"{month} (no data)"
        for i, month in enumerate(month_names)
    ]

    # making the actual buttons
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

    # show line plot for given year and month, if there is data associated with that month
    if selected_month and "(no data)" not in selected_month:
        month_number = month_names.index(selected_month)

        filtered_pdf = pdf[
            (pdf["timestamp"].dt.month == month_number + 1)
            & (pdf["timestamp"].dt.year == selected_year)
        ]

        if not filtered_pdf.empty:
            fig, ax = plt.subplots(figsize=(12, 6))

            for (from_zone, to_zone), group in filtered_pdf.groupby(
                ["from_zone", "to_zone"]
            ):
                group = group.sort_values("timestamp")
                ax.plot(
                    group["timestamp"],
                    group["flow_mw"],
                    marker="o",
                    label=f"{from_zone} → {to_zone}",
                )

            start = pd.Timestamp(selected_year, month_number + 1, 1)
            end = start + pd.offsets.MonthBegin(1)
            ax.set_xlim(start, end)

            ax.set_xlabel("Date")
            ax.set_ylabel("Average power flow (MW)")
            ax.set_title(f"Average Power Flows — {selected_month} {selected_year}")
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis="x", rotation=45)
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            fig.tight_layout()

            st.pyplot(fig)
    # explain to the user why they dont see a plot and tell them what to do
    else:
        st.info("Select a month with available data.")

# explain data source for both plots on right and left side:
with st.expander("Data source"):
    st.write(
        "The data comes from the MongoDB database `power_data`.\n\n"
        "- **Flow distribution (pie chart):** Collection `annual_flows`, "
        "containing annual aggregated power flows between zones for 2025.\n\n"
        "- **Average power flows (line chart):** Collection "
        "`daily_average_flows`, containing daily average power flows "
        "between zones, with timestamps used to filter by year and month."
    )
