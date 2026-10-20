import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

from utils import Buttons
from styling import style_funcs

Buttons.home_button()
st.title("Reservoir data")


# Load data
from NVE_API import get_nve_data

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

# Fetch data to determine available months
df = get_nve_data()
df["date"] = pd.to_datetime(df["date"])

months = sorted(df["date"].dt.to_period("M").unique())
month_labels = [str(m) for m in months]

selected_months = st.select_slider(
    "Select download interval",
    options=month_labels,
    value=(month_labels[0], month_labels[-1]),
)

slider_start = pd.Period(selected_months[0]).start_time
slider_end = pd.Period(selected_months[1]).end_time

# Filter/download selected interval
df = get_nve_data(
    start_date=slider_start,
    end_date=slider_end,
)

plot_df = df

# Decide which columns to plot
if selected == "All":
    selected_cols = y_axis_cols
else:
    selected_cols = [selected]

# Standardize selected variables
scaler = StandardScaler()

plot_df[selected_cols] = scaler.fit_transform(plot_df[selected_cols])

# Create the large figure
fig = plt.figure(figsize=(12, 10))
gs = fig.add_gridspec(2, 2, height_ratios=[2, 1])

# --------------------------------------------------
# 1. Variables over time
# --------------------------------------------------

ax = fig.add_subplot(gs[0, :])

for col in selected_cols:
    ax.scatter(plot_df["date"], plot_df[col], s=0.3, label=col)

ax.set_xlabel("Date")
ax.set_ylabel("Standardized value (z-score)")
ax.set_title("Standardized reservoir data over time")
ax.legend()
ax.grid(True)

# --------------------------------------------------
# 2. Variables by area type
# --------------------------------------------------

ax = fig.add_subplot(gs[1, 0])

for i, col in enumerate(selected_cols):
    data = [group[col].dropna() for _, group in plot_df.groupby("area type")]

    ax.boxplot(data, positions=range(len(data)))

ax.set_xlabel("Area type")
ax.set_ylabel("Standardized value")
ax.set_title("By area type")

# --------------------------------------------------
# 3. Variables by area number
# --------------------------------------------------

ax = fig.add_subplot(gs[1, 1])

for col in selected_cols:
    data = [group[col].dropna() for _, group in plot_df.groupby("area number")]

    ax.boxplot(data)

ax.set_xlabel("Area number")
ax.set_ylabel("Standardized value")
ax.set_title("By area number")

plt.tight_layout()

st.pyplot(fig)


style_funcs.style_selectbox()
style_funcs.style_slider()
