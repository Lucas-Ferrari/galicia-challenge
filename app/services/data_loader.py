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
        """Load routes from CSV file with individual record processing"""
        created_count = 0
        errors = []

        try:
            # Leer CSV con manejo de valores nulos
            df = pd.read_csv(file_path, sep="|", na_values=['\\N', 'NULL', ''])

            print(f"Total rows in CSV: {len(df)}")
            print(f"Columns: {df.columns.tolist()}")

            # Cache de aeropuertos existentes para validación rápida
            existing_airports = set()
            try:
                airport_query = self.db.execute("SELECT id FROM airports")
                existing_airports = {row[0] for row in airport_query.fetchall()}
                print(f"Found {len(existing_airports)} airports in database")
            except Exception as e:
                print(f"Warning: Could not load airports for validation: {e}")

            for index, row in df.iterrows():
                try:
                    # Validar que no haya valores nulos en campos críticos
                    if pd.isna(row["AeropuertoDestinoID"]) or pd.isna(row["AeropuertoOrigenID"]):
                        errors.append(f"Row {index + 2}: Missing airport ID (Origin: {row['AeropuertoOrigenID']}, Destination: {row['AeropuertoDestinoID']})")
                        continue

                    origin_id = int(row["AeropuertoOrigenID"])
                    destination_id = int(row["AeropuertoDestinoID"])

                    # Validar que los aeropuertos existan (solo si tenemos el cache)
                    if existing_airports:
                        if origin_id not in existing_airports:
                            errors.append(f"Row {index + 2}: Origin airport ID {origin_id} not found in database")
                            continue
                        if destination_id not in existing_airports:
                            errors.append(f"Row {index + 2}: Destination airport ID {destination_id} not found in database")
                            continue

                    # Convertir fecha
                    flight_date = datetime.strptime(
                        str(row["Fecha"]), "%Y-%m-%d"
                    ).date()

                    route_data = {
                        "airline_code": str(row["CodAerolinea"]).strip(),
                        "airline_id": int(row["IDAerolinea"]),
                        "origin_code": str(row["AeropuertoOrigen"]).strip(),
                        "origin_id": origin_id,
                        "destination_code": str(row["AeropuertoDestino"]).strip(),
                        "destination_id": destination_id,
                        "tickets_sold": int(row["TicketsVendidos"]),
                        "total_seats": int(row["Lugares"]),
                        "flight_date": flight_date,
                    }

                    # Validaciones básicas
                    if route_data["tickets_sold"] > route_data["total_seats"]:
                        errors.append(f"Row {index + 2}: Tickets sold ({route_data['tickets_sold']}) exceeds seats ({route_data['total_seats']})")
                        continue

                    if route_data["total_seats"] <= 0:
                        errors.append(f"Row {index + 2}: Invalid total seats ({route_data['total_seats']})")
                        continue

                    # Crear y agregar ruta con commit individual
                    try:
                        route = Route(**route_data)
                        self.db.add(route)
                        self.db.commit()
                        created_count += 1

                        # Log cada 100 registros procesados
                        if created_count % 100 == 0:
                            print(f"Successfully processed {created_count} routes...")

                    except Exception as commit_error:
                        # Rollback solo este registro y continuar
                        self.db.rollback()
                        error_detail = str(commit_error)
                        if "foreign key constraint" in error_detail:
                            errors.append(f"Row {index + 2}: Foreign key violation - Airport ID not found (Origin: {origin_id}, Destination: {destination_id})")
                        else:
                            errors.append(f"Row {index + 2}: Database error - {error_detail}")
                        continue

                except ValueError as ve:
                    errors.append(f"Row {index + 2}: Value conversion error - {str(ve)}")
                    continue
                except Exception as e:
                    errors.append(f"Row {index + 2}: Unexpected error - {str(e)}")
                    continue

            print(f"Load completed: {created_count} routes successfully loaded")

            # Mostrar resumen de errores
            if errors:
                print(f"Found {len(errors)} errors:")

                # Agrupar errores por tipo para mejor análisis
                error_types = {}
                for error in errors:
                    if "Foreign key violation" in error:
                        error_types["Foreign Key Violations"] = error_types.get("Foreign Key Violations", 0) + 1
                    elif "Missing airport ID" in error:
                        error_types["Missing Airport IDs"] = error_types.get("Missing Airport IDs", 0) + 1
                    elif "Tickets sold exceeds seats" in error:
                        error_types["Data Validation"] = error_types.get("Data Validation", 0) + 1
                    else:
                        error_types["Other"] = error_types.get("Other", 0) + 1

                print("Error summary:")
                for error_type, count in error_types.items():
                    print(f"  - {error_type}: {count}")

                # Mostrar los primeros 10 errores específicos
                print("\nFirst 10 specific errors:")
                for error in errors[:10]:
                    print(f"  - {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")
            else:
                print("No errors found!")

        except Exception as e:
            error_msg = f"File processing error: {str(e)}"
            errors.append(error_msg)
            print(error_msg)

        return created_count, errors
