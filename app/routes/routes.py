from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional
import math

from app.database import get_db
from app.services.routes import RouteService
from app.schemas.route import MostFlownByCountryList

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get(
    "/most_flown_by_country",
    response_model=MostFlownByCountryList,
    description="Get top 5 most flown routes per country within a date range",
)
async def get_most_flown_by_country(
    date_from: Optional[date] = Query(
        default=None, description="Start date (YYYY-MM-DD). Defaults to today"
    ),
    date_to: Optional[date] = Query(
        default=None, description="End date (YYYY-MM-DD). Defaults to today"
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number for pagination",
    ),
    page_size: int = Query(
        default=25,
        ge=1,
        le=100,
        description="Number of countries per page",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns the top 5 most flown routes for each country.
    Routes are grouped by origin airport's country.

    - **date_from**: Start date for filtering (defaults to today)
    - **date_to**: End date for filtering (defaults to today)
    - **page**: Page number starting at 1
    - **page_size**: Number of countries per page (default 25, max 100)

    Returns a paginated list of countries with their top 5 routes sorted by flight count.
    """
    # Default to today if not provided
    today = date.today()
    if date_from is None:
        date_from = today
    if date_to is None:
        date_to = today

    route_service = RouteService(db)
    countries, total_countries = route_service.get_most_flown_by_country(
        date_from=date_from, date_to=date_to, top_n=5, page=page, page_size=page_size
    )

    total_pages = math.ceil(total_countries / page_size) if total_countries > 0 else 0

    return MostFlownByCountryList(
        date_from=date_from,
        date_to=date_to,
        countries=countries,
        page=page,
        page_size=page_size,
        total_countries=total_countries,
        total_pages=total_pages,
    )
