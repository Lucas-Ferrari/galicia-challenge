from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, index=True)
    code = Column(String(10), nullable=True, unique=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Integer, nullable=True, index=True)

    def __repr__(self):
        return f"<Airport(id={self.id}, code='{self.code}', name='{self.name}')>"
