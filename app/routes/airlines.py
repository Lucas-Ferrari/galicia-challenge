from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import math

from app.database import get_db
from app.schemas.airline import (
    AirlineOccupancyResponse,
    ConsecutiveHighOccupancyResponse,
)
from app.services.airlines import AirlineService

router = APIRouter(prefix="/airlines", tags=["airlines"])


@router.get(
    "/occupancy_average",
    response_model=AirlineOccupancyResponse,
    description="Get average occupancy rate for by airline"
)
async def get_occupancy_average(
    date_from: Optional[date] = Query(
        default=None,
        description="Start date (YYYY-MM-DD). If not provided, includes all dates",
    ),
    date_to: Optional[date] = Query(
        default=None,
        description="End date (YYYY-MM-DD). If not provided, includes all dates",
    ),
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(
        default=25, ge=1, le=100, description="Number of airlines per page (max 100)"
    ),
    db: Session = Depends(get_db),
):
    """
    Returns the average occupancy rate for each airline.

    The occupancy rate is calculated as:
    **avg_occupancy = total_tickets_sold / total_seats**

    - **date_from**: Optional start date for filtering
    - **date_to**: Optional end date for filtering
    - **page**: Page number starting at 1
    - **page_size**: Number of airlines per page (default 25, max 100)

    If no dates are provided, calculates occupancy for all flights in the database.

    Results are sorted by occupancy rate (highest first) and paginated.
    """
    airline_service = AirlineService(db)
    airlines, total_airlines = airline_service.get_occupancy_average(
        date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )

    total_pages = math.ceil(total_airlines / page_size) if total_airlines > 0 else 0

    return AirlineOccupancyResponse(
        date_from=date_from,
        date_to=date_to,
        airlines=airlines,
        page=page,
        page_size=page_size,
        total_airlines=total_airlines,
        total_pages=total_pages,
    )


@router.get(
    "/consecutive_high_occupancy_routes",
    response_model=ConsecutiveHighOccupancyResponse,
    description="Get airlines that have flown the same route with high occupancy on consecutive days",
)
async def get_consecutive_high_occupancy_routes(
    date_from: Optional[date] = Query(
        default=None,
        description="Start date (YYYY-MM-DD). If not provided, includes all dates",
    ),
    date_to: Optional[date] = Query(
        default=None,
        description="End date (YYYY-MM-DD). If not provided, includes all dates",
    ),
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(
        default=25, ge=1, le=100, description="Number of airlines per page (max 100)"
    ),
    db: Session = Depends(get_db),
):
    """
    Returns airlines that have flown the same route with high occupancy (>=85%)
    on **consecutive days**.

    For example, if an airline flies JFK->LAX with >=85% occupancy on:
    - June 1st, 2nd, 3rd (3 consecutive days)
    - June 10th, 11th (2 consecutive days)

    Both sequences will be reported.

    - **date_from**: Optional start date for filtering
    - **date_to**: Optional end date for filtering
    - **page**: Page number starting at 1
    - **page_size**: Number of airlines per page (default 25, max 100)

    Results are sorted by the number of consecutive route sequences (descending).
    """
    airline_service = AirlineService(db)

    airlines, total_airlines = airline_service.get_consecutive_high_occupancy_routes(
        date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )

    total_pages = math.ceil(total_airlines / page_size) if total_airlines > 0 else 0

    return ConsecutiveHighOccupancyResponse(
        date_from=date_from,
        date_to=date_to,
        high_occupancy_threshold=0.85,
        airlines=airlines,
        page=page,
        page_size=page_size,
        total_airlines=total_airlines,
        total_pages=total_pages,
    )
