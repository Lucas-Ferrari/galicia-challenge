from pydantic import BaseModel, Field
from datetime import date
from typing import List


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


class MostFlownRoute(BaseModel):
    """Schema for most flown route"""

    origin_code: str
    destination_code: str
    origin_name: str
    destination_name: str
    flight_count: int = Field(..., description="Number of flights on this route")

    class Config:
        from_attributes = True


class MostFlownByCountryResponse(BaseModel):
    """Response for most flown routes by country"""

    country: str
    routes: List[MostFlownRoute]

    class Config:
        from_attributes = True


class MostFlownByCountryList(BaseModel):
    """List response wrapper"""

    date_from: date
    date_to: date
    countries: List[MostFlownByCountryResponse]
    page: int
    page_size: int
    total_countries: int
    total_pages: int
