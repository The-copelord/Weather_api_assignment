import os
import requests
from pathlib import Path
from typing import List
from models import WeatherStats, ErrorResponse, CityWeather, CityComparison
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.inmemory import InMemoryBackend
from datetime import timezone
from contextlib import asynccontextmanager

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="weather-cache")
    yield
   
    
app = FastAPI(title="Weather Data Analyzer API", lifespan=lifespan)

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY") or "2e4928286d1375202901c21ed0810fd0"
print("API KEY:", API_KEY)
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

@app.get("/")
def read_root():
    return {"Welcome to the Weather Data Analyzer API!"}

@app.get("/weather", response_model=WeatherStats, responses={404: {"model": ErrorResponse}})
@cache(expire=300) 
def get_weather(city: str = Query(..., description="City name to fetch weather data")):
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

    now = datetime.now(timezone.utc)
    five_days_after = now - timedelta(days=5)

    for item in data.get("list", []):
        timestamp = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
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
    
    return WeatherStats(
        average_temperature=avg_temp,
        highest_temperature=max_temp,
        lowest_temperature=min_temp,
        weather_summary=unique_conditions
    )

@app.get("/compare", response_model=CityComparison)
@cache(expire=300)
def compare_weather(city1: str = Query(...), city2: str = Query(...)):

    city1 = city1.strip().lower()
    city2 = city2.strip().lower()
    city1, city2 = sorted([city1, city2])

    def fetch_city_weather(city):
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(BASE_URL, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found or API error")

        data = response.json()
        temperatures = []
        conditions = []

        now = datetime.now(timezone.utc)
        five_days_ago = now - timedelta(days=5)
        for item in data.get("list", []):
            timestamp = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            if timestamp >= five_days_ago:
                temp = item["main"]["temp"]
                weather = item["weather"][0]["main"]
                temperatures.append(temp)
                conditions.append(weather)

        if not temperatures:
            raise HTTPException(status_code=404, detail=f"No weather data available for city '{city}'")

        return CityWeather(
            city=city,
            average_temperature=round(sum(temperatures) / len(temperatures), 2),
            highest_temperature=max(temperatures),
            lowest_temperature=min(temperatures),
            weather_summary=list(set(conditions))
        )

    return CityComparison(
        city1=fetch_city_weather(city1),
        city2=fetch_city_weather(city2)
    )
