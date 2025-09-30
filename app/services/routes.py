from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from datetime import date

from app.models.airline import Airline
from app.models.route import Route
from app.models.airport import Airport

from app.schemas.route import (
    MostFlownRoute,
    MostFlownByCountryResponse,
    DomesticFlightDetail,
    DomesticHighOccupancyAltitudeDeltaWithDetails,
)

from app.config import settings

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

    def get_domestic_high_occupancy_altitude_delta(
        self,
        date_from: date = None,
        date_to: date = None,
        page: int = 1,
        page_size: int = 25
    ) -> DomesticHighOccupancyAltitudeDeltaWithDetails:
        """
        Calculate percentage of domestic flights with:
        - Occupancy rate >= 85% (from settings)
        - Altitude difference between origin and destination > 1000m (from settings)

        A domestic flight is one where origin and destination are in the same country.
        Returns paginated list of flights meeting criteria.

        Args:
            date_from: Optional start date for filtering (defaults to today)
            date_to: Optional end date for filtering (defaults to today)
            page: Page number (1-indexed)
            page_size: Number of flights per page (default 25)

        Returns:
            Report with statistics and paginated flight details
        """
        today = date.today()
        if date_from is None:
            date_from = today
        if date_to is None:
            date_to = today

        occupancy_threshold = settings.high_occupancy_threshold
        altitude_threshold = settings.min_altitude

        origin = Airport.__table__.alias('origin')
        destination = Airport.__table__.alias('destination')

        query = (
            self.db.query(
                func.count(Route.id).label('total_domestic'),
                func.sum(
                    case(
                        (
                            and_(
                                (Route.tickets_sold / Route.total_seats) >= occupancy_threshold,
                                func.abs(origin.c.altitude - destination.c.altitude) > altitude_threshold
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('meeting_criteria')
            )
            .join(origin, Route.origin_id == origin.c.id)
            .join(destination, Route.destination_id == destination.c.id)
            .filter(
                and_(
                    Route.flight_date >= date_from,
                    Route.flight_date <= date_to,
                    origin.c.country == destination.c.country,  # Domestic flights only
                    Route.total_seats > 0  # Avoid division by zero
                )
            )
        )

        result = query.first()

        total_domestic = result.total_domestic or 0
        meeting_criteria = result.meeting_criteria or 0

        if total_domestic > 0:
            percentage = (meeting_criteria / total_domestic) * 100
        else:
            percentage = 0.0

        flights_query = (
            self.db.query(
                Route.id.label('route_id'),
                Route.airline_code,
                Airline.name.label('airline_name'),
                Route.origin_code,
                origin.c.name.label('origin_name'),
                origin.c.altitude.label('origin_altitude'),
                Route.destination_code,
                destination.c.name.label('destination_name'),
                destination.c.altitude.label('destination_altitude'),
                func.abs(origin.c.altitude - destination.c.altitude).label('altitude_delta'),
                origin.c.country,
                Route.flight_date,
                Route.tickets_sold,
                Route.total_seats,
                (Route.tickets_sold / Route.total_seats).label('occupancy_rate')
            )
            .join(origin, Route.origin_id == origin.c.id)
            .join(destination, Route.destination_id == destination.c.id)
            .join(Airline, Route.airline_id == Airline.id)
            .filter(
                and_(
                    Route.flight_date >= date_from,
                    Route.flight_date <= date_to,
                    origin.c.country == destination.c.country,
                    Route.total_seats > 0,
                    (Route.tickets_sold / Route.total_seats) >= occupancy_threshold,
                    func.abs(origin.c.altitude - destination.c.altitude) > altitude_threshold
                )
            )
            .order_by(Route.flight_date.desc(), Route.id)
        )

        offset = (page - 1) * page_size
        paginated_flights = flights_query.limit(page_size).offset(offset).all()

        flight_details = []
        for flight in paginated_flights:
            occupancy_rate = flight.occupancy_rate
            flight_detail = DomesticFlightDetail(
                route_id=flight.route_id,
                airline_code=flight.airline_code,
                airline_name=flight.airline_name,
                origin_code=flight.origin_code,
                origin_name=flight.origin_name,
                origin_altitude=flight.origin_altitude,
                destination_code=flight.destination_code,
                destination_name=flight.destination_name,
                destination_altitude=flight.destination_altitude,
                altitude_delta=flight.altitude_delta,
                country=flight.country,
                flight_date=flight.flight_date,
                occupancy_rate=round(occupancy_rate, 4),
                occupancy_percentage=round(occupancy_rate * 100, 2),
                tickets_sold=flight.tickets_sold,
                total_seats=flight.total_seats
            )
            flight_details.append(flight_detail)

        import math
        total_pages = math.ceil(meeting_criteria / page_size) if meeting_criteria > 0 else 0

        return DomesticHighOccupancyAltitudeDeltaWithDetails(
            date_from=date_from,
            date_to=date_to,
            total_domestic_flights=total_domestic,
            flights_meeting_criteria=meeting_criteria,
            percentage=round(percentage, 2),
            high_occupancy_threshold=occupancy_threshold,
            altitude_delta_threshold=altitude_threshold,
            flights=flight_details,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
