from pydantic import BaseModel
from typing import Optional


class Airline(BaseModel):
    """Airline schema for responses"""

    id: int
    name: str
    iata_code: Optional[str] = None
    country: Optional[str] = None
    active: bool = True

    class Config:
        from_attributes = True


class AirlineOccupancyStats(BaseModel):
    """Airline occupancy statistics"""

    airline_id: int
    airline_name: str
    iata_code: Optional[str] = None
    total_flights: int
    average_occupancy: float

    class Config:
        from_attributes = True
