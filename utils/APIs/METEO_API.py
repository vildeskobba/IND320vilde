import openmeteo_requests
import pandas as pd
import requests_cache

from retry_requests import retry


def download_weather(
    coordinates: dict, region: str, start_date: str, end_date: str, batch_size=100
):
    print(
        f"starting download of hourly data for {region} between {start_date} and {end_date}..."
    )

    locations = coordinates[region]
    all_data = []
    url = "https://archive-api.open-meteo.com/v1/archive"

    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    for start in range(0, len(locations), batch_size):
        batch = locations.iloc[start : start + batch_size]

        lons = batch["longitude"].tolist()
        lats = batch["latitude"].tolist()

        params = {
            "latitude": ",".join(map(str, lats)),
            "longitude": ",".join(map(str, lons)),
            "start_date": start_date,
            "end_date": end_date,
            "hourly": [
                "temperature_2m",
                "precipitation",
            ],
            "models": "era5",
            "timezone": "Europe/Oslo",
        }

        responses = openmeteo.weather_api(url, params=params, timeout=30)
        for i, response in enumerate(responses):
            hourly = response.Hourly()

            data = {
                "time": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(
                        "Europe/Oslo"
                    ),
                    periods=hourly.Variables(0).ValuesAsNumpy().size,
                    freq="h",
                ),
                "latitude": lats[i],
                "longitude": lons[i],
                "temperature": hourly.Variables(0).ValuesAsNumpy(),
                "precipitation": hourly.Variables(1).ValuesAsNumpy(),
            }

            all_data.append(pd.DataFrame(data))
        print(
            f"Downloaded {min(start + batch_size, len(locations))}/{len(locations)} locations"
        )

    return pd.concat(all_data, ignore_index=True)
