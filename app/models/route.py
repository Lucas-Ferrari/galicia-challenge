from sqlalchemy import Column, Integer, String, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)

    # Airline information
    airline_code = Column(String(10), nullable=False, index=True)
    airline_id = Column(Integer, ForeignKey("airlines.id"), nullable=False, index=True)

    # Airport information
    origin_code = Column(String(10), nullable=False, index=True)
    origin_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    destination_code = Column(String(10), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("airports.id"), nullable=False)

    # Capacity and occupancy
    tickets_sold = Column(Integer, nullable=False)
    total_seats = Column(Integer, nullable=False)

    # Date
    flight_date = Column(Date, nullable=False, index=True)

    # Relationships
    airline = relationship("Airline", backref="routes")
    origin_airport = relationship(
        "Airport", foreign_keys=[origin_id], backref="departing_routes"
    )
    destination_airport = relationship(
        "Airport", foreign_keys=[destination_id], backref="arriving_routes"
    )

    @property
    def occupancy_rate(self) -> float:
        """Calculate occupancy rate"""
        if self.total_seats == 0:
            return 0.0
        return self.tickets_sold / self.total_seats

    @property
    def is_high_occupancy(self) -> bool:
        """Check if route has high occupancy (>=85%)"""
        return self.occupancy_rate >= 0.85

    def __repr__(self):
        return f"<Route(id={self.id}, {self.origin_code}->{self.destination_code}, date={self.flight_date})>"


Index("idx_route_airline_date", Route.airline_id, Route.flight_date)
Index("idx_route_origin_dest", Route.origin_id, Route.destination_id)
