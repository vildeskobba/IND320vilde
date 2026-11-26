import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler

from utils.utils import Buttons
from styling import style_funcs

Buttons.home_button()
st.title("Reservoir data")

# Load data function, via API
from utils.APIs.NVE_API import get_nve_data

# Columns that can be plotted
y_axis_cols = [
    "reservoir level",
    "capacity (TWh)",
    "level (TWh)",
    "reservoir level last week",
    "change level",
]

# Select what to plot
selected = st.selectbox("Select data to plot", ["All"] + y_axis_cols)

# Fetch data
df = get_nve_data()
df["date"] = pd.to_datetime(df["date"])

months = sorted(df["date"].dt.to_period("M").unique())
month_labels = [str(m) for m in months]

selected_months = st.select_slider(
    "Select download interval",
    options=month_labels,
    value=(month_labels[-12], month_labels[-1]),
)

slider_start = pd.Period(selected_months[0]).start_time
slider_end = pd.Period(selected_months[1]).end_time

# Filter/download selected interval
df = get_nve_data(
    start_date=slider_start,
    end_date=slider_end,
)

plot_df = df.copy()

# Decide which columns to plot
if selected == "All":
    selected_cols = y_axis_cols
else:
    selected_cols = [selected]

# Standardize selected variables
scaler = StandardScaler()
plot_df[selected_cols] = scaler.fit_transform(plot_df[selected_cols])

# --------------------------------------------------
# 1. Variables over time
# --------------------------------------------------

st.subheader("Standardized reservoir data over time")

long_df = plot_df.melt(
    id_vars=["date"],
    value_vars=selected_cols,
    var_name="Variable",
    value_name="Standardized value",
)

fig_time = px.scatter(
    long_df,
    x="date",
    y="Standardized value",
    color="Variable",
    title="Standardized reservoir data over time",
    opacity=0.7,
)

fig_time.update_traces(marker=dict(size=3))

fig_time.update_layout(
    xaxis_title="Date",
    yaxis_title="Standardized value (z-score)",
    hovermode="x unified",
    height=500,
)

st.plotly_chart(fig_time, use_container_width=True)

# --------------------------------------------------
# 2. Variables by area type
# --------------------------------------------------

st.subheader("Reservoir data by area type")

area_type_df = plot_df.melt(
    id_vars=["area type"],
    value_vars=selected_cols,
    var_name="Variable",
    value_name="Standardized value",
)

fig_area_type = px.box(
    area_type_df,
    x="area type",
    y="Standardized value",
    color="Variable",
    title="Reservoir data by area type",
)

fig_area_type.update_layout(
    xaxis_title="Area type",
    yaxis_title="Standardized value",
    boxmode="group",
    height=450,
)

st.plotly_chart(fig_area_type, use_container_width=True)

# --------------------------------------------------
# 3. Variables by area number
# --------------------------------------------------

st.subheader("Reservoir data by area number")

area_number_df = plot_df.melt(
    id_vars=["area number"],
    value_vars=selected_cols,
    var_name="Variable",
    value_name="Standardized value",
)

fig_area_number = px.box(
    area_number_df,
    x="area number",
    y="Standardized value",
    color="Variable",
    title="Reservoir data by area number",
)

fig_area_number.update_layout(
    xaxis_title="Area number",
    yaxis_title="Standardized value",
    boxmode="group",
    height=450,
)

st.plotly_chart(fig_area_number, use_container_width=True)

# Styling
style_funcs.style_selectbox()
style_funcs.style_slider()
