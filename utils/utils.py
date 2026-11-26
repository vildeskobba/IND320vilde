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


def forecast_reservoir(
    magasin_df,
    entso_df=None,
    weather_df=None,
    exchange_df=None,
    area="NO_1",
    model_type="sarimax",
    history_weeks=200,
    horizon_weeks=4,
    data_sources=("weather", "entso", "exchange"),
    target="reservoir_level",
    model_params=None,
):
    """
    Forecast reservoir filling for one Norwegian region.

    Parameters
    ----------
    magasin_df : DataFrame
        Magasinstatistikk data.
    entso_df : DataFrame
        ENTSO-E electricity flow data.
    weather_df : DataFrame
        Weekly weather data.
    exchange_df : DataFrame
        Weekly exchange rate data.
    area : str
        Norwegian reservoir area (NO_1 to NO_5).
    model_type : str
        "river" or "sarimax".
    history_weeks : int
        Number of historical weeks used for training.
    horizon_weeks : int
        Number of weeks to forecast.
    data_sources : tuple
        External data sources to include.
    target : str
        "reservoir_level" or "level_TWh".
    model_params : dict
        Model-specific parameters.

    Returns
    -------
    DataFrame
        Weekly reservoir filling predictions.
    """

    if model_params is None:
        model_params = {}

    # --------------------------------------------------
    # 1. Prepare weekly reservoir data
    # --------------------------------------------------

    df = magasin_df[magasin_df["area"] == area].copy()

    df["date"] = [
        date.fromisocalendar(int(y), int(w), 1)
        for y, w in zip(df["iso_year"], df["iso_week"])
    ]

    df["date"] = pd.to_datetime(df["date"])

    df = df.set_index("date").sort_index()

    df = df[[target]].copy()

    # --------------------------------------------------
    # 2. Prepare optional external data sources
    # --------------------------------------------------

    if "weather" in data_sources and weather_df is not None:
        weather = weather_df[weather_df["area"] == area].copy()

        weather["date"] = pd.to_datetime(
            [
                date.fromisocalendar(int(y), int(w), 1)
                for y, w in zip(weather["iso_year"], weather["iso_week"])
            ]
        )

        weather = weather.set_index("date").sort_index()

        weather = weather[["temperature", "precipitation"]]

        df = df.join(weather, how="left")

    if "entso" in data_sources and entso_df is not None:
        entso = entso_df.copy()

        entso["date"] = pd.to_datetime(
            [
                date.fromisocalendar(int(y), int(w), 1)
                for y, w in zip(entso["iso_year"], entso["iso_week"])
            ]
        )

        incoming = (
            entso[entso["to_zone"] == area]
            .groupby("date")["flow_mw"]
            .sum()
            .rename("incoming_flow")
        )

        outgoing = (
            entso[entso["from_zone"] == area]
            .groupby("date")["flow_mw"]
            .sum()
            .rename("outgoing_flow")
        )

        flows = pd.concat([incoming, outgoing], axis=1).fillna(0)

        flows["net_flow"] = flows["incoming_flow"] - flows["outgoing_flow"]

        df = df.join(flows, how="left")

    if "exchange" in data_sources and exchange_df is not None:
        exchange = exchange_df.copy()

        exchange["date"] = pd.to_datetime(
            [
                date.fromisocalendar(int(y), int(w), 1)
                for y, w in zip(exchange["iso_year"], exchange["iso_week"])
            ]
        )

        exchange = exchange.set_index("date").sort_index()

        df = df.join(exchange[["OBS_VALUE"]], how="left")

    # --------------------------------------------------
    # 3. Create continuous weekly time series
    # --------------------------------------------------

    df = df[~df.index.duplicated(keep="last")]

    weekly_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq="W-MON")

    df = df.reindex(weekly_index)

    # Avoid using future information when filling gaps.
    external_cols = [c for c in df.columns if c != target]

    if external_cols:
        df[external_cols] = df[external_cols].ffill().fillna(0)

    df = df.dropna(subset=[target])

    # Use only the requested amount of history.
    df = df.tail(history_weeks)

    if len(df) < 12:
        raise ValueError("At least 12 historical observations are required.")

    # --------------------------------------------------
    # 4. River lag-based machine learning
    # --------------------------------------------------

    if model_type.lower() == "river":
        from river import preprocessing, linear_model

        l2 = model_params.get("l2", 0.01)

        model = preprocessing.StandardScaler() | linear_model.LinearRegression(l2=l2)

        external_cols = [c for c in df.columns if c != target]

        values = df[target].astype(float).tolist()

        def create_features(history, external, week):

            features = {
                "lag_1": history[-1],
                "lag_2": history[-2],
                "lag_3": history[-3],
                "lag_4": history[-4],
                "mean_4": np.mean(history[-4:]),
                "mean_13": np.mean(history[-13:])
                if len(history) >= 13
                else np.mean(history),
                "week_sin": np.sin(2 * np.pi * week / 52),
                "week_cos": np.cos(2 * np.pi * week / 52),
            }

            if len(history) >= 52:
                features["lag_52"] = history[-52]

            for col in external_cols:
                features[col] = float(external[col])

            return features

        # Train sequentially using past observations.
        for i in range(13, len(df)):
            history = values[:i]

            features = create_features(
                history, df.iloc[i][external_cols], df.index[i].isocalendar().week
            )

            model.learn_one(features, values[i])

        # Recursive multi-step forecasting.
        history = values.copy()
        last_external = (
            df.iloc[-1][external_cols] if external_cols else pd.Series(dtype=float)
        )

        predictions = []

        for step in range(1, horizon_weeks + 1):
            future_date = df.index[-1] + pd.Timedelta(weeks=step)

            features = create_features(
                history, last_external, future_date.isocalendar().week
            )

            prediction = model.predict_one(features)

            # Reservoir filling cannot be negative.
            prediction = max(0, prediction)

            # Keep the predicted value for future lags.
            history.append(prediction)
            predictions.append(prediction)

    # --------------------------------------------------
    # 5. SARIMAX alternative
    # --------------------------------------------------

    elif model_type.lower() == "sarimax":
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        order = model_params.get("order", (1, 1, 1))

        seasonal_order = model_params.get("seasonal_order", (0, 0, 0, 0))

        external_cols = [c for c in df.columns if c != target]

        y = df[target].astype(float)

        exog = df[external_cols] if external_cols else None

        future_exog = None

        if exog is not None:
            future_exog = pd.DataFrame(
                np.repeat(exog.iloc[[-1]].values, horizon_weeks, axis=0),
                columns=external_cols,
            )

        model = SARIMAX(
            y,
            exog=exog,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )

        fitted_model = model.fit(disp=False, maxiter=2000, method="powell")

        if not fitted_model.mle_retvals["converged"]:
            print("WARNING: SARIMAX did not converge")

        predictions = fitted_model.forecast(
            steps=horizon_weeks, exog=future_exog
        ).tolist()

        predictions = [max(0, float(p)) for p in predictions]

    else:
        raise ValueError("model_type must be 'river' or 'sarimax'.")

    # --------------------------------------------------
    # 6. Return forecast DataFrame
    # --------------------------------------------------

    future_dates = pd.date_range(
        start=df.index[-1] + pd.Timedelta(weeks=1), periods=horizon_weeks, freq="W-MON"
    )

    result = pd.DataFrame(
        {
            "date": future_dates,
            "iso_year": [d.isocalendar().year for d in future_dates],
            "iso_week": [d.isocalendar().week for d in future_dates],
            "area": area,
            "predicted_filling": predictions,
        }
    )

    if target == "reservoir_level":
        result["predicted_filling"] = result["predicted_filling"].clip(0, 1)

    return result
