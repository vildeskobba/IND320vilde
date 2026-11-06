import requests
import pandas as pd


# Function to get data from the NVE API with optional start and end date filters
def get_nve_data(start_date=None, end_date=None):
    NVE_URL = (
        "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"
    )

    response = requests.get(NVE_URL, timeout=60)
    response.raise_for_status()

    df = pd.DataFrame(response.json())

    # Convert Date column to datetime format, not like i did in ca_1, but like the student i peer reviewed, because her way was better:)
    df["dato_Id"] = pd.to_datetime(df["dato_Id"])

    # Filter the DataFrame based on the provided start and end dates
    if start_date is not None:
        df = df[df["dato_Id"] >= pd.to_datetime(start_date)]

    if end_date is not None:
        df = df[df["dato_Id"] <= pd.to_datetime(end_date)]

    df = df.rename(
        columns={
            "dato_Id": "date",
            "omrType": "area type",
            "omrnr": "area number",
            "iso_aar": "year (ISO)",
            "iso_uke": "week (ISO)",
            "fyllingsgrad": "reservoir level",
            "kapasitet_TWh": "capacity (TWh)",
            "fylling_TWh": "level (TWh)",
            "neste_Publiseringsdato": "next publishing date",
            "fyllingsgrad_forrige_uke": "reservoir level last week",
            "endring_fyllingsgrad": "change level",
        }
    )

    return df.sort_values("date").reset_index(drop=True)
