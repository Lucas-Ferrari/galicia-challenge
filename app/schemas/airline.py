from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class Airline(BaseModel):
    """Airline schema for responses"""

    id: int
    name: str
    alias: Optional[str] = None
    iata_code: Optional[str] = None
    icao_code: Optional[str] = None
    callsign: Optional[str] = None
    country: Optional[str] = None
    active: bool = True

    class Config:
        from_attributes = True


class AirlineOccupancy(BaseModel):
    """Schema for airline occupancy statistics"""

    airline_id: int
    airline_name: str
    airline_code: str
    country: Optional[str] = None
    avg_occupancy_rate: float = Field(..., description="Average occupancy rate as decimal (0.85 = 85%)")
    avg_occupancy_percentage: float = Field(..., description="Average occupancy as percentage (85.00)")
    total_flights: int = Field(..., description="Total number of flights")
    total_seats: int = Field(..., description="Total seats across all flights")
    total_tickets_sold: int = Field(..., description="Total tickets sold")

    class Config:
        from_attributes = True


class AirlineOccupancyResponse(BaseModel):
    """Response wrapper for airline occupancy"""

    date_from: Optional[date] = None
    date_to: Optional[date] = None
    airlines: List[AirlineOccupancy]
    total_airlines: int
    page: int
    page_size: int
    total_pages: int
