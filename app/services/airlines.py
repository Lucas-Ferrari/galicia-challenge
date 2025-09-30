from sqlalchemy.orm import Session
from sqlalchemy import and_, cast, Numeric, func
from typing import List, Dict, Any, Optional
from datetime import date

from app.models.airline import Airline
from app.models.route import Route
from app.schemas.airline import AirlineOccupancy


class AirlineServiceError(Exception):
    """Base exception for airline service errors"""


class DatabaseConnectionError(AirlineServiceError):
    """Raised when database connection fails"""


class DataProcessingError(AirlineServiceError):
    """Raised when data processing fails"""


class AirlineService:
    """Service for airline operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_airlines_with_high_occupancy_consecutive_routes(
        self, min_occupancy: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Get airlines that operated routes with high occupancy on consecutive days

        Args:
            min_occupancy: Minimum occupancy percentage (default 0.85 for 85%)

        Returns:
            List of airline dictionaries with their consecutive high-occupancy routes

        Raises:
            DatabaseConnectionError: When database query fails
            DataProcessingError: When data processing fails
        """
        try:
            high_occupancy_data = self._fetch_high_occupancy_flights(min_occupancy)

            airlines_with_routes = self._process_consecutive_sequences_by_airline(
                high_occupancy_data
            )

            return airlines_with_routes

        except Exception as e:
            if "database" in str(e).lower() or "connection" in str(e).lower():
                raise DatabaseConnectionError(f"Database query failed: {str(e)}")
            else:
                raise DataProcessingError(f"Data processing failed: {str(e)}")

    def get_occupancy_average(
            self,
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
            page: int = 1,
            page_size: int = 25
    ) -> tuple[List[AirlineOccupancy], int]:
        """
        Calculate average occupancy rate for each airline with pagination.

        Formula: avg_occupancy = sum(tickets_sold) / sum(total_seats)

        Args:
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            page: Page number (1-indexed)
            page_size: Number of airlines per page (default 25)

        Returns:
            Tuple of (list of airlines with occupancy statistics, total airline count)
        """
        query = self.db.query(
            Airline.id.label("airline_id"),
            Airline.name.label("airline_name"),
            Airline.iata_code.label("airline_code"),
            Airline.country,
            func.sum(Route.tickets_sold).label("total_tickets_sold"),
            func.sum(Route.total_seats).label("total_seats"),
            func.count(Route.id).label("total_flights"),
        ).join(Route, Airline.id == Route.airline_id)

        filters = []
        if date_from:
            filters.append(Route.flight_date >= date_from)
        if date_to:
            filters.append(Route.flight_date <= date_to)

        if filters:
            query = query.filter(and_(*filters))

        query = query.group_by(
            Airline.id, Airline.name, Airline.iata_code, Airline.country
        )

        query = query.order_by(
            (func.sum(Route.tickets_sold) / func.sum(Route.total_seats)).desc()
        )

        results = query.all()

        occupancy_list = []
        for row in results:
            if row.total_seats > 0:
                avg_occupancy_rate = row.total_tickets_sold / row.total_seats
            else:
                avg_occupancy_rate = 0.0

            occupancy = AirlineOccupancy(
                airline_id=row.airline_id,
                airline_name=row.airline_name,
                airline_code=row.airline_code or "N/A",
                country=row.country,
                avg_occupancy_rate=round(avg_occupancy_rate, 4),
                avg_occupancy_percentage=round(avg_occupancy_rate * 100, 2),
                total_flights=row.total_flights,
                total_seats=row.total_seats,
                total_tickets_sold=row.total_tickets_sold,
            )
            occupancy_list.append(occupancy)

        total_airlines = len(occupancy_list)

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_list = occupancy_list[start_idx:end_idx]

        return paginated_list, total_airlines

    def _fetch_high_occupancy_flights(
        self, min_occupancy: float
    ) -> List[Dict[str, Any]]:
        """
        Fetch flights with high occupancy from database

        Args:
            min_occupancy: Minimum occupancy percentage

        Returns:
            List of flight data dictionaries
        """
        try:
            query_result = (
                self.db.query(
                    Route.airline_code,
                    Airline.name.label("airline_name"),
                    Route.origin_code,
                    Route.destination_code,
                    Route.flight_date,
                    (
                        cast(Route.tickets_sold, Numeric)
                        / cast(Route.total_seats, Numeric)
                        * 100
                    ).label("occupancy_pct"),
                )
                .join(Airline, Route.airline_id == Airline.id)
                .filter(
                    and_(
                        Route.total_seats > 0,
                        cast(Route.tickets_sold, Numeric)
                        / cast(Route.total_seats, Numeric)
                        >= min_occupancy,
                    )
                )
                .order_by(
                    Route.airline_code,
                    Route.origin_code,
                    Route.destination_code,
                    Route.flight_date,
                )
                .all()
            )

            return [
                {
                    "airline_code": row.airline_code,
                    "airline_name": row.airline_name,
                    "origin_code": row.origin_code,
                    "destination_code": row.destination_code,
                    "flight_date": row.flight_date,
                    "occupancy_pct": float(row.occupancy_pct),
                }
                for row in query_result
            ]

        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to fetch high occupancy flights: {str(e)}"
            )

    def _process_consecutive_sequences_by_airline(
        self, flights_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process flight data to find consecutive day sequences grouped by airline

        Args:
            flights_data: List of flight data dictionaries

        Returns:
            List of airline dictionaries with their consecutive routes
        """
        try:
            airline_groups = self._group_flights_by_airline(flights_data)

            airlines_with_consecutive_routes = []

            for (airline_code, airline_name), airline_flights in airline_groups.items():
                route_groups = self._group_flights_by_route_only(airline_flights)

                consecutive_routes = []
                for (origin_code, destination_code), flights in route_groups.items():
                    sequences = self._find_consecutive_sequences(flights)

                    for sequence in sequences:
                        route_dict = self._create_route_sequence_dict(
                            origin_code, destination_code, sequence
                        )
                        consecutive_routes.append(route_dict)

                if consecutive_routes:
                    airline_dict = {
                        "airline_code": airline_code,
                        "airline_name": airline_name,
                        "routes": consecutive_routes,
                        "total_routes": len(consecutive_routes),
                    }
                    airlines_with_consecutive_routes.append(airline_dict)

            return airlines_with_consecutive_routes

        except Exception as e:
            raise DataProcessingError(
                f"Failed to process consecutive sequences by airline: {str(e)}"
            )

    def _group_flights_by_airline(
        self, flights_data: List[Dict[str, Any]]
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """Group flights by airline"""
        airline_groups = {}

        for flight in flights_data:
            key = (flight["airline_code"], flight["airline_name"])

            if key not in airline_groups:
                airline_groups[key] = []

            airline_groups[key].append(flight)

        return airline_groups

    def _group_flights_by_route_only(
        self, flights_data: List[Dict[str, Any]]
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """Group flights by route (origin-destination) for a single airline"""
        route_groups = {}

        for flight in flights_data:
            key = (flight["origin_code"], flight["destination_code"])

            if key not in route_groups:
                route_groups[key] = []

            route_groups[key].append(
                {"date": flight["flight_date"], "occupancy": flight["occupancy_pct"]}
            )

        for key in route_groups:
            route_groups[key].sort(key=lambda x: x["date"])

        return route_groups

    def _find_consecutive_sequences(
        self, flights: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Find consecutive day sequences in flights"""
        if len(flights) < 2:
            return []

        consecutive_sequences = []
        current_sequence = [flights[0]]

        for i in range(1, len(flights)):
            current_date = flights[i]["date"]
            previous_date = flights[i - 1]["date"]

            if (current_date - previous_date).days == 1:
                current_sequence.append(flights[i])
            else:
                if len(current_sequence) >= 2:
                    consecutive_sequences.append(current_sequence.copy())
                current_sequence = [flights[i]]

        if len(current_sequence) >= 2:
            consecutive_sequences.append(current_sequence)

        return consecutive_sequences

    def _create_route_sequence_dict(
        self, origin_code: str, destination_code: str, sequence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create route sequence dictionary"""
        consecutive_dates = [
            {
                "flight_date": flight["date"],
                "occupancy_percentage": round(flight["occupancy"], 2),
            }
            for flight in sequence
        ]

        return {
            "origin_code": origin_code,
            "destination_code": destination_code,
            "route": f"{origin_code}-{destination_code}",
            "consecutive_dates": consecutive_dates,
            "total_consecutive_days": len(consecutive_dates),
        }
