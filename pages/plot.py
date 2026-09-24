import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

from utils import Buttons 
from utils import load_data
from styling import style_funcs

Buttons.home_button()
st.title("Reservoir data")


# Load data
df = load_data("reservoirs.csv")
df["date"] = pd.to_datetime(df["date"])

# Columns that can be plotted
y_axis_cols = [
    "reservoir level",
    "capacity (TWh)",
    "level (TWh)",
    "reservoir level last week",
    "change level"
]



# Select what to plot
selected = st.selectbox(
    "Select data to plot",
    ["All"] + y_axis_cols
)

# Select months
months = sorted(df["date"].dt.to_period("M").unique())
month_labels = [str(month) for month in months]

# Default: last 10 years
default_start = months[-121]
default_end = months[-1]


selected_months = st.select_slider(
    "Select months",
    options=month_labels,
    value=(str(default_start), str(default_end))
)

start_month = pd.Period(selected_months[0])
end_month = pd.Period(selected_months[1])

# Filter data
plot_df = df[
    (df["date"].dt.to_period("M") >= start_month) &
    (df["date"].dt.to_period("M") <= end_month)
].copy()

# Decide which columns to plot
if selected == "All":
    selected_cols = y_axis_cols
else:
    selected_cols = [selected]

# Standardize selected variables
scaler = StandardScaler()

plot_df[selected_cols] = scaler.fit_transform(
    plot_df[selected_cols]
)

# Create the large figure
fig = plt.figure(figsize=(12, 10))
gs = fig.add_gridspec(2, 2, height_ratios=[2, 1])

# --------------------------------------------------
# 1. Variables over time
# --------------------------------------------------

ax = fig.add_subplot(gs[0, :])

for col in selected_cols:
    ax.scatter(
        plot_df["date"],
        plot_df[col],
        s=0.3,
        label=col
    )

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
    data = [
        group[col].dropna()
        for _, group in plot_df.groupby("area type")
    ]

    ax.boxplot(
        data,
        positions=range(len(data))
    )

ax.set_xlabel("Area type")
ax.set_ylabel("Standardized value")
ax.set_title("By area type")

# --------------------------------------------------
# 3. Variables by area number
# --------------------------------------------------

ax = fig.add_subplot(gs[1, 1])

for col in selected_cols:
    data = [
        group[col].dropna()
        for _, group in plot_df.groupby("area number")
    ]

    ax.boxplot(data)

ax.set_xlabel("Area number")
ax.set_ylabel("Standardized value")
ax.set_title("By area number")

plt.tight_layout()

st.pyplot(fig)


style_funcs.style_selectbox() 
style_funcs.style_slider()