import streamlit as st
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import STL
import numpy as np
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from scipy.fft import dct, idct

from styling import style_funcs


class Buttons:
    @staticmethod
    def home_button():
        if st.button("", icon=":material/home:", key="home_button"):
            st.switch_page("pages/home.py")
        style_funcs.style_home_button()


@st.cache_data
def load_data(file_name):
    file_path = Path(__file__).parent / file_name
    reservoirs_df = pd.read_csv(file_path)
    reservoirs_df.columns = [
        "date",
        "area type",
        "area number",
        "year (ISO)",
        "week (ISO)",
        "reservoir level",
        "capacity (TWh)",
        "level (TWh)",
        "next publishing date",
        "reservoir level last week",
        "change level",
    ]
    return reservoirs_df


def plot_stl(data, seasonal=13, trend=None, robust=True, period=365):
    # Prepare time series
    series = data.set_index("date")["reservoir level"].sort_index()

    # Perform STL decomposition
    stl = STL(series, period=period, seasonal=seasonal, trend=trend, robust=robust)

    result = stl.fit()

    # Plot decomposition
    fig = result.plot()
    fig.set_size_inches(14, 9)
    fig.suptitle("STL decomposition of degree of filling", y=1.02)

    plt.tight_layout()

    return fig


def plot_spectrogram(data, window_length=365, overlap=300):
    # Prepare time series
    series = data.set_index("date")["reservoir level"].sort_index().dropna()

    values = series.to_numpy()

    # Calculate spectrogram
    frequencies, times, power = spectrogram(
        values,
        fs=1,  # One observation per day
        nperseg=window_length,
        noverlap=overlap,
    )

    # Plot
    fig, ax = plt.subplots(figsize=(14, 6))

    mesh = ax.pcolormesh(
        times, frequencies, 10 * np.log10(power + 1e-12), shading="auto"
    )

    fig.colorbar(mesh, ax=ax, label="Power (dB)")
    ax.set_title("Spectrogram of reservoir level")
    ax.set_xlabel("Time (days from start)")
    ax.set_ylabel("Frequency (cycles per day)")

    plt.tight_layout()

    return fig


def plot_temperature_anomalies(weather_data, contamination=0.01, n_neighbors=20):
    if weather_data.empty:
        st.write("There is no data for the selected area.")
        fig, ax = plt.subplots(figsize=(14, 6))
        return fig, pd.DataFrame()
    # Calculate average temperature across locations
    temperature = (
        weather_data.groupby("time")["temperature"].mean().sort_index().dropna()
    )

    # LOF expects a 2D array
    X = temperature.to_numpy().reshape(-1, 1)

    # Detect anomalies
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    predictions = lof.fit_predict(X)
    anomaly_mask = predictions == -1

    # Plot
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(temperature.index, temperature, label="Average temperature", linewidth=0.8)

    ax.scatter(
        temperature.index[anomaly_mask],
        temperature[anomaly_mask],
        color="red",
        label="Anomalies (LOF)",
        zorder=3,
    )

    ax.set_title("Average temperature and detected anomalies")
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (°C)")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()

    # Summarise anomalies
    anomaly_summary = pd.DataFrame(
        {
            "time": temperature.index[anomaly_mask],
            "temperature": temperature[anomaly_mask],
            "LOF score": lof.negative_outlier_factor_[anomaly_mask],
        }
    )

    return fig, anomaly_summary


def plot_precipitation_outliers(weather_data, cutoff=30, n_std=3):
    """
    Plot average precipitation and identify outliers using
    high-pass DCT filtering and robust SPC boundaries.

    Parameters
    ----------
    weather_data : DataFrame
        Must contain time, precipitation, latitude and longitude.
    cutoff : int
        Number of low-frequency DCT coefficients to remove.
    n_std : float
        Number of robust standard deviations for SPC boundaries.

    Returns
    -------
    fig : matplotlib Figure
    outlier_summary : DataFrame
    """
    if weather_data.empty:
        st.write("There is no data for the selected area.")
        fig, ax = plt.subplots(figsize=(14, 6))
        return fig, pd.DataFrame()
    # Average precipitation across all locations
    precipitation = weather_data.groupby("time")["precipitation"].mean().sort_index()

    x = precipitation.to_numpy()

    # DCT high-pass filtering
    coefficients = dct(x, norm="ortho")
    coefficients[:cutoff] = 0

    satv = idct(coefficients, norm="ortho")

    # Robust statistics
    median = np.median(satv)
    mad = np.median(np.abs(satv - median))

    robust_std = 1.4826 * mad

    upper = median + n_std * robust_std
    lower = median - n_std * robust_std

    # Identify outliers
    outliers = (satv > upper) | (satv < lower)

    # Plot original precipitation
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(precipitation.index, x, label="Average precipitation", linewidth=0.8)

    ax.scatter(
        precipitation.index[outliers],
        x[outliers],
        color="red",
        label="Outliers",
        zorder=3,
    )

    ax.set_title("Average precipitation and detected outliers")
    ax.set_xlabel("Time")
    ax.set_ylabel("Precipitation (mm)")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()

    # Outlier summary
    outlier_summary = pd.DataFrame(
        {
            "time": precipitation.index[outliers],
            "precipitation": x[outliers],
            "SATV": satv[outliers],
        }
    )

    return fig, outlier_summary
