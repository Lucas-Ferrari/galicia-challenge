import csv
import pandas as pd
from datetime import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.airport import Airport
from app.models.airline import Airline
from app.models.route import Route
from app.database import SessionLocal


class DataLoader:
    """Service for loading data from CSV files"""

    def __init__(self):
        self.db = SessionLocal()

    def close(self):
        self.db.close()

    def load_airports_from_dat(self, file_path: str) -> Tuple[int, int, List[str]]:
        """Load airports from .dat file"""
        created_count = 0
        updated_count = 0
        errors = []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                # Skip header if exists
                first_line = file.readline().strip()
                if not first_line.split(",")[0].isdigit():
                    pass  # Has header
                else:
                    file.seek(0)  # No header, reset

                for line_num, line in enumerate(file, 1):
                    try:
                        parts = line.strip().split(",")
                        if len(parts) < 8:
                            errors.append(f"Line {line_num}: Insufficient columns")
                            continue

                        airport_data = {
                            "id": int(parts[0]),
                            "name": parts[1].strip('"'),
                            "city": parts[2].strip('"'),
                            "country": parts[3].strip('"'),
                            "code": parts[4].strip('"') if parts[4] != "\\N" else None,
                            "latitude": float(parts[5]) if parts[5] != "\\N" else None,
                            "longitude": float(parts[6]) if parts[6] != "\\N" else None,
                            "altitude": (
                                int(float(parts[7])) if parts[7] != "\\N" else None
                            ),
                        }

                        existing = (
                            self.db.query(Airport)
                            .filter(Airport.id == airport_data["id"])
                            .first()
                        )

                        if existing:
                            for key, value in airport_data.items():
                                if key != "id":
                                    setattr(existing, key, value)
                            updated_count += 1
                        else:
                            airport = Airport(**airport_data)
                            self.db.add(airport)
                            created_count += 1

                    except Exception as e:
                        errors.append(f"Line {line_num}: {str(e)}")
                        continue

                self.db.commit()

        except Exception as e:
            self.db.rollback()
            errors.append(f"File error: {str(e)}")

        return created_count, updated_count, errors

    def load_airlines_from_csv(self, file_path: str) -> Tuple[int, int, List[str]]:
        """Load airlines from CSV file"""
        created_count = 0
        updated_count = 0
        errors = []

        try:
            df = pd.read_csv(file_path)

            for index, row in df.iterrows():
                try:
                    airline_data = {
                        "id": int(row["IDAerolinea"]),
                        "name": str(row["NombreAerolinea"]).strip(),
                        "iata_code": (
                            str(row["IATA"]).strip()
                            if pd.notna(row["IATA"]) and row["IATA"] != "-"
                            else None
                        ),
                        "country": (
                            str(row["Pais"]).strip() if pd.notna(row["Pais"]) else None
                        ),
                        "active": (
                            str(row["Activa"]).upper() == "Y"
                            if pd.notna(row["Activa"])
                            else True
                        ),
                    }

                    existing = (
                        self.db.query(Airline)
                        .filter(Airline.id == airline_data["id"])
                        .first()
                    )

                    if existing:
                        for key, value in airline_data.items():
                            if key != "id":
                                setattr(existing, key, value)
                        updated_count += 1
                    else:
                        airline = Airline(**airline_data)
                        self.db.add(airline)
                        created_count += 1

                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    continue

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            errors.append(f"File error: {str(e)}")

        return created_count, updated_count, errors

    def load_routes_from_csv(self, file_path: str) -> Tuple[int, List[str]]:
        """Load routes from CSV file"""
        created_count = 0
        errors = []

        try:
            df = pd.read_csv(file_path, sep="|")

            for index, row in df.iterrows():
                try:
                    flight_date = datetime.strptime(
                        str(row["Fecha"]), "%Y-%m-%d"
                    ).date()

                    route_data = {
                        "airline_code": str(row["CodAerolinea"]).strip(),
                        "airline_id": int(row["IDAerolinea"]),
                        "origin_code": str(row["AeropuertoOrigen"]).strip(),
                        "origin_id": int(row["AeropuertoOrigenID"]),
                        "destination_code": str(row["AeropuertoDestino"]).strip(),
                        "destination_id": int(row["AeropuertoDestinoID"]),
                        "tickets_sold": int(row["TicketsVendidos"]),
                        "total_seats": int(row["Lugares"]),
                        "flight_date": flight_date,
                    }

                    # Basic validation
                    if route_data["tickets_sold"] > route_data["total_seats"]:
                        errors.append(f"Row {index + 2}: Tickets sold exceeds seats")
                        continue

                    route = Route(**route_data)
                    self.db.add(route)
                    created_count += 1

                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    continue

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            errors.append(f"File error: {str(e)}")

        return created_count, errors
