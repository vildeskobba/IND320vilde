import requests

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 59.91,
    "longitude": 10.75,
    "hourly": "temperature_2m,precipitation",
    "timezone": "Europe/Oslo",
}

response = requests.get(url, params=params)

data = response.json()

print(data)
