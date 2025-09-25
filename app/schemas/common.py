from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


class DateRange(BaseModel):
    """Date range filter"""

    start_date: date
    end_date: date


class FileUploadResponse(BaseModel):
    """File upload response"""

    filename: str
    records_processed: int
    records_created: int
    records_updated: int
    errors: List[str] = []
