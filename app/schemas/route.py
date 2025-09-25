from pydantic import BaseModel
from datetime import date
from typing import Optional


class Route(BaseModel):
    """Route schema for responses"""

    id: int
    airline_code: str
    origin_code: str
    destination_code: str
    tickets_sold: int
    total_seats: int
    flight_date: date
    occupancy_rate: float

    class Config:
        from_attributes = True


class ConsecutiveHighOccupancyRoute(BaseModel):
    """Consecutive high occupancy routes"""

    airline_id: int
    airline_name: str
    route_key: str
    origin_code: str
    destination_code: str
    consecutive_days: int
    start_date: date
    end_date: date


class DomesticFlightStats(BaseModel):
    """Domestic flight statistics"""

    total_high_occupancy_flights: int
    domestic_high_occupancy_flights: int
    domestic_high_altitude_flights: int
    percentage_domestic: float
    percentage_domestic_high_altitude: float
    meets_criteria: bool


class TopRoute(BaseModel):
    """Top routes by country"""

    rank: int
    route_key: str
    origin_code: str
    destination_code: str
    flight_count: int
