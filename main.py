import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from typing import List
from models import WeatherStats, ErrorResponse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv



load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app = FastAPI(title="Weather Data Analyzer API")

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
print("Check if key is being loaded:", os.environ.get("OPENWEATHERMAP_API_KEY"))
API_KEY ="2e4928286d1375202901c21ed0810fd0"
print("API KEY:", API_KEY)
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

@app.get("/weather", response_model=WeatherStats, responses={404: {"model": ErrorResponse}})
def get_weather(city: str = Query(..., description="City name to fetch weather data")):
    """
    Fetches and analyzes the last 5 days of weather data for a given city.
    Calculates average, highest, and lowest temperature, and summarizes weather conditions.
    """
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="City not found or API error")

    data = response.json()

    temperatures = []
    conditions = []

    now = datetime.utcnow()
    five_days_ago = now - timedelta(days=5)

    for item in data.get("list", []):
        timestamp = datetime.utcfromtimestamp(item["dt"])
        if timestamp >= five_days_ago:
            temp = item["main"]["temp"]
            weather = item["weather"][0]["main"]
            temperatures.append(temp)
            conditions.append(weather)

    if not temperatures:
        raise HTTPException(status_code=404, detail="No weather data available for the past 5 days")

    avg_temp = round(sum(temperatures) / len(temperatures), 2)
    max_temp = max(temperatures)
    min_temp = min(temperatures)
    unique_conditions = list(set(conditions))

    return WeatherStats(
        average_temperature=avg_temp,
        highest_temperature=max_temp,
        lowest_temperature=min_temp,
        weather_summary=unique_conditions
    )
