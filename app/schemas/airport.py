from pydantic import BaseModel
from typing import Optional, List


class Airport(BaseModel):
    """Airport schema for responses"""

    id: int
    name: str
    city: str
    country: str
    iata_code: Optional[str] = None  # Código IATA (3 letras)
    icao_code: Optional[str] = None  # Código ICAO (4 letras)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[int] = None
    utc_offset: Optional[float] = None
    continent_code: Optional[str] = None
    timezone: Optional[str] = None

    class Config:
        from_attributes = True


class AirportUpload(BaseModel):
    """Schema for bulk airport upload from file"""

    airports_data: str


class AirportImportResponse(BaseModel):
    """Airport import response"""

    filename: str
    total_records: int
    records_inserted: int
    records_skipped_duplicate: int
    records_skipped_error: int
    errors: List[str] = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_records == 0:
            return 0.0
        return (self.records_inserted / self.total_records) * 100
