from pydantic import BaseModel
from typing import Optional


class Airport(BaseModel):
    """Airport schema for responses"""

    id: int
    name: str
    city: str
    country: str
    code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[int] = None

    class Config:
        from_attributes = True


class AirportUpload(BaseModel):
    """Schema for bulk airport upload from file"""

    airports_data: str
