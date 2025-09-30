from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, datetime
from app.models.route import Route
from app.models.airport import Airport
from app.schemas.route import MostFlownRoute, MostFlownByCountryResponse


class RouteService:
    """Service for route operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_most_flown_by_country(
        self,
        date_from: date,
        date_to: date,
        top_n: int = 5,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[List[MostFlownByCountryResponse], int]:
        """
        Get top N most flown routes for each country within a date range.
        Groups by origin country with pagination.

        Args:
            date_from: Start date for filtering
            date_to: End date for filtering
            top_n: Number of top routes per country (default 5)
            page: Page number (1-indexed)
            page_size: Number of countries per page (default 25)

        Returns:
            Tuple of (list of countries with their top routes, total country count)
        """
        # Query to get flight counts per route and origin country
        route_counts = (
            self.db.query(
                Airport.country.label("country"),
                Route.origin_code,
                Route.destination_code,
                func.max(Airport.name).label("origin_name"),  # Get origin airport name
                func.count(Route.id).label("flight_count"),
            )
            .join(Airport, Route.origin_id == Airport.id)
            .filter(and_(Route.flight_date >= date_from, Route.flight_date <= date_to))
            .group_by(Airport.country, Route.origin_code, Route.destination_code)
            .order_by(Airport.country, func.count(Route.id).desc())
            .all()
        )

        # Get destination airport names in a separate query for efficiency
        destination_names = self._get_airport_names_map()

        # Group by country and take top N per country
        countries_dict: Dict[str, List[MostFlownRoute]] = {}

        for row in route_counts:
            country = row.country

            if country not in countries_dict:
                countries_dict[country] = []

            # Only add if we haven't reached top_n for this country
            if len(countries_dict[country]) < top_n:
                route = MostFlownRoute(
                    origin_code=row.origin_code,
                    destination_code=row.destination_code,
                    origin_name=row.origin_name,
                    destination_name=destination_names.get(
                        row.destination_code, row.destination_code
                    ),
                    flight_count=row.flight_count,
                )
                countries_dict[country].append(route)

        # Convert to response format
        result = [
            MostFlownByCountryResponse(country=country, routes=routes)
            for country, routes in countries_dict.items()
        ]

        # Sort by country name for consistent output
        result.sort(key=lambda x: x.country)

        # Store total count before pagination
        total_countries = len(result)

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_result = result[start_idx:end_idx]

        return paginated_result, total_countries

    def _get_airport_names_map(self) -> Dict[str, str]:
        """
        Get a mapping of airport codes to names for efficient lookups
        Returns dict with both IATA and ICAO codes as keys
        """
        airports = self.db.query(
            Airport.iata_code, Airport.icao_code, Airport.name
        ).all()

        name_map = {}
        for airport in airports:
            if airport.iata_code:
                name_map[airport.iata_code] = airport.name
            if airport.icao_code:
                name_map[airport.icao_code] = airport.name

        return name_map
