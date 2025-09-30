from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Airline(Base):
    __tablename__ = "airlines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    alias = Column(String(255), nullable=True)  # New field
    iata_code = Column(String(10), nullable=True, index=True)
    icao_code = Column(String(10), nullable=True, index=True)
    callsign = Column(String(100), nullable=True)  # New field
    country = Column(String(100), nullable=True, index=True)
    active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Airline(id={self.id}, iata='{self.iata_code}', name='{self.name}')>"
