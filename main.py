import os
from pathlib import Path
from typing import List
from models import WeatherStats, ErrorResponse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.inmemory import InMemoryBackend
from cachetools import TTLCache

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app = FastAPI(title="Weather Data Analyzer API")
@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend(), prefix="weather-cache")
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
API_KEY ="2e4928286d1375202901c21ed0810fd0"
print("API KEY:", API_KEY)
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"
weather_cache = TTLCache(maxsize=100, ttl=300)
@app.get("/")
def read_root():
    return {"Welcome to the Weather Data Analyzer API!"}

@app.get("/weather", response_model=WeatherStats, responses={404: {"model": ErrorResponse}})
@cache(expire=300)  # Caches for 5 minutes
def get_weather(city: str = Query(..., description="City name to fetch weather data")):
    if city in weather_cache:
        print("Returning cached result for:", city)
        return weather_cache[city]
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
    five_days_after = now - timedelta(days=5)

    for item in data.get("list", []):
        timestamp = datetime.utcfromtimestamp(item["dt"])
        if timestamp >= five_days_after:
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
    result = WeatherStats(
        average_temperature=avg_temp,
        highest_temperature=max_temp,
        lowest_temperature=min_temp,
        weather_summary=unique_conditions
    )
    # Store in cache
    weather_cache[city] = result

    return result