from datetime import date
from typing import Optional
from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, func

from app.models.route import Route
from app.models.airport import Airport
from app.schemas.analytics import DomesticFlightAnalysis
from app.config import settings


class AnalyticsService:
    """Service for flight analytics operations"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_domestic_flights(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> DomesticFlightAnalysis:
        """
        Generate report for domestic flights with high occupancy and altitude differences

        Logic:
        1. Get all flights with occupancy ≥85%
        2. Check which are domestic (same country origin-destination)
        3. Check which domestic flights have altitude difference >1000m
        4. Calculate percentages
        """

        origin_airport = aliased(Airport)
        dest_airport = aliased(Airport)

        base_query = (
            self.db.query(
                Route,
                origin_airport.country.label("origin_country"),
                dest_airport.country.label("dest_country"),
                origin_airport.altitude.label("origin_altitude"),
                dest_airport.altitude.label("dest_altitude"),
            )
            .join(origin_airport, Route.origin_id == origin_airport.id)
            .join(dest_airport, Route.destination_id == dest_airport.id)
        )

        if start_date:
            base_query = base_query.filter(Route.flight_date >= start_date)
        if end_date:
            base_query = base_query.filter(Route.flight_date <= end_date)

        high_occupancy_flights = base_query.filter(
            (Route.tickets_sold * 1.0 / Route.total_seats)
            >= settings.high_occupancy_threshold
        ).all()

        total_high_occupancy = len(high_occupancy_flights)

        if total_high_occupancy == 0:
            return DomesticFlightAnalysis(
                total_high_occupancy_flights=0,
                domestic_high_occupancy_flights=0,
                domestic_high_altitude_flights=0,
                percentage_domestic=0.0,
                percentage_domestic_high_altitude=0.0,
                meets_criteria=False,
            )

        domestic_count = 0
        high_altitude_count = 0

        for (
            route,
            origin_country,
            dest_country,
            origin_alt,
            dest_alt,
        ) in high_occupancy_flights:
            if origin_country and dest_country and origin_country == dest_country:
                domestic_count += 1

                if origin_alt is not None and dest_alt is not None:
                    altitude_diff = abs(origin_alt - dest_alt)
                    if altitude_diff > settings.min_altitude:
                        high_altitude_count += 1

        # Calculate percentages
        percentage_domestic = (
            (domestic_count / total_high_occupancy * 100)
            if total_high_occupancy > 0
            else 0.0
        )
        percentage_domestic_high_altitude = (
            (high_altitude_count / domestic_count * 100) if domestic_count > 0 else 0.0
        )

        # Check if meets criteria (≥85% domestic AND altitude difference exists)
        meets_criteria = percentage_domestic >= 85.0 and high_altitude_count > 0

        return DomesticFlightAnalysis(
            total_high_occupancy_flights=total_high_occupancy,
            domestic_high_occupancy_flights=domestic_count,
            domestic_high_altitude_flights=high_altitude_count,
            percentage_domestic=round(percentage_domestic, 2),
            percentage_domestic_high_altitude=round(
                percentage_domestic_high_altitude, 2
            ),
            meets_criteria=meets_criteria,
        )
