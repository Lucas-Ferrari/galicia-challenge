from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.database import get_db
from app.services.analytics import AnalyticsService
from app.schemas.analytics import DomesticFlightAnalysis

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/domestic-flights", response_model=DomesticFlightAnalysis)
async def analyze_domestic_flights(
    start_date: Optional[date] = Query(
        None, description="Start date filter (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Analyze domestic flights with high occupancy and altitude differences

    Returns:
    - Total high occupancy flights (≥85%)
    - How many of those are domestic (same country origin-destination)
    - How many domestic flights have altitude difference >1000m
    - Percentages and criteria compliance
    """

    try:
        analytics_service = AnalyticsService(db)
        result = analytics_service.analyze_domestic_flights(start_date, end_date)

    except Exception:
        raise HTTPException(
            status_code=400, 
            detail="Service unavailable. Try later.")


    return result
