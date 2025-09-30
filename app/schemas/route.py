from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


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


class DomesticHighOccupancyAltitudeDelta(BaseModel):
    """Response for domestic high occupancy altitude delta report"""

    date_from: Optional[date] = None
    date_to: Optional[date] = None
    total_domestic_flights: int = Field(
        ..., description="Total number of domestic flights"
    )
    flights_meeting_criteria: int = Field(
        ..., description="Flights with occupancy >= 85% and altitude delta > 1000m"
    )
    percentage: float = Field(..., description="Percentage of flights meeting criteria")
    high_occupancy_threshold: float = Field(
        default=0.85, description="Occupancy threshold used (default 0.85)"
    )
    altitude_delta_threshold: int = Field(
        default=1000,
        description="Altitude difference threshold in meters (default 1000)",
    )


class DomesticFlightDetail(BaseModel):
    """Detail of a specific domestic flight meeting criteria"""

    route_id: int
    airline_code: str
    airline_name: Optional[str] = None
    origin_code: str
    origin_name: str
    origin_altitude: Optional[int] = None
    destination_code: str
    destination_name: str
    destination_altitude: Optional[int] = None
    altitude_delta: int = Field(
        ..., description="Absolute altitude difference in meters"
    )
    country: str
    flight_date: date
    occupancy_rate: float
    occupancy_percentage: float
    tickets_sold: int
    total_seats: int

    class Config:
        from_attributes = True


class DomesticHighOccupancyAltitudeDeltaWithDetails(BaseModel):
    """Response with pagination and flight details"""

    date_from: Optional[date] = None
    date_to: Optional[date] = None
    total_domestic_flights: int
    flights_meeting_criteria: int
    percentage: float
    high_occupancy_threshold: float
    altitude_delta_threshold: int
    flights: List[DomesticFlightDetail] = Field(
        default=[], description="List of flights meeting criteria"
    )
    page: int
    page_size: int
    total_pages: int
