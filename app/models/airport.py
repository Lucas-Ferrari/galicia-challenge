from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, index=True)
    iata_code = Column(String(10), nullable=True, index=True)
    icao_code = Column(String(10), nullable=True, unique=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Integer, nullable=True, index=True)
    utc_offset = Column(Float, nullable=True)
    continent_code = Column(String(10), nullable=True)
    timezone = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Airport(id={self.id}, iata='{self.iata_code}', icao='{self.icao_code}', name='{self.name}')>"

    def is_valid(self) -> tuple[bool, list[str]]:
        """
        Rudimentary serializer, validate the airport instance against model constraints.
        Should split into mindividual field serializers.
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not self.name or len(self.name.strip()) == 0:
            errors.append(f"Airport {self.id}: name is required")
        elif len(self.name) > 255:
            errors.append(f"Airport {self.id}: name exceeds 255 characters")

        if not self.city or len(self.city.strip()) == 0:
            errors.append(f"Airport {self.id}: city is required")
        elif len(self.city) > 100:
            errors.append(f"Airport {self.id}: city exceeds 100 characters")

        if not self.country or len(self.country.strip()) == 0:
            errors.append(f"Airport {self.id}: country is required")
        elif len(self.country) > 100:
            errors.append(f"Airport {self.id}: country exceeds 100 characters")

        # Check optional field lengths
        if self.iata_code and len(self.iata_code) > 20:
            errors.append(f"Airport {self.id}: iata_code exceeds 20 characters")

        if self.icao_code and len(self.icao_code) > 20:
            errors.append(f"Airport {self.id}: icao_code exceeds 20 characters")

        if self.continent_code and len(self.continent_code) > 20:
            errors.append(f"Airport {self.id}: continent_code exceeds 20 characters")

        if self.timezone and len(self.timezone) > 100:
            errors.append(f"Airport {self.id}: timezone exceeds 100 characters")

        # Check coordinate ranges
        if self.latitude is not None and (self.latitude < -90 or self.latitude > 90):
            errors.append(f"Airport {self.id}: latitude must be between -90 and 90")

        if self.longitude is not None and (
            self.longitude < -180 or self.longitude > 180
        ):
            errors.append(f"Airport {self.id}: longitude must be between -180 and 180")

        if self.utc_offset is not None and (
            self.utc_offset < -12 or self.utc_offset > 14
        ):
            errors.append(f"Airport {self.id}: utc_offset must be between -12 and 14")

        return len(errors) == 0, errors
