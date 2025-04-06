from pydantic import BaseModel
from typing import List

class WeatherStats(BaseModel):
    average_temperature: float
    highest_temperature: float
    lowest_temperature: float
    weather_summary: List[str]

class ErrorResponse(BaseModel):
    detail: str
