from pydantic import BaseModel
from datetime import date
from typing import Optional


class DomesticFlightAnalysis(BaseModel):
    """
    Analysis of domestic flights with high occupancy and altitude difference
    meets_criteria if ≥85% domestic AND >1000m altitude diff
    """

    total_high_occupancy_flights: int
    domestic_high_occupancy_flights: int
    domestic_high_altitude_flights: int
    percentage_domestic: float
    percentage_domestic_high_altitude: float
    meets_criteria: bool

    class Config:
        from_attributes = True


class DateRangeFilter(BaseModel):
    """Optional date range filter"""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
