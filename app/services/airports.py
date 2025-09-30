from typing import List, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.airport import Airport
from app.schemas.airport import AirportImportResponse


class AirportService:
    """Service for airport operations"""

    def __init__(self, db: Session):
        self.db = db

    def import_airports_from_file_content(
        self, file_content: str, filename: str
    ) -> AirportImportResponse:
        """
        Import airports from file content (.dat format) using batch processing
        """
        response = AirportImportResponse(
            filename=filename,
            total_records=0,
            records_inserted=0,
            records_skipped_duplicate=0,
            records_skipped_error=0,
            errors=[],
        )

        # Get existing airport codes to check for duplicates
        existing_codes = self._get_existing_airport_codes()

        # Parse file content
        lines = file_content.strip().split("\n")

        # Skip header if exists
        start_line = 0
        if lines and not lines[0].split(",")[0].isdigit():
            start_line = 1

        data_lines = lines[start_line:]
        response.total_records = len(data_lines)

        # Process in batches of 50
        batch_size = 50
        processed_codes = {"icao": set(), "iata": set()}
        processed_ids = set()  # Track IDs in current session

        for i in range(0, len(data_lines), batch_size):
            batch_lines = data_lines[i : i + batch_size]
            batch_result = self._process_batch(
                batch_lines,
                start_line + i + 1,  # Actual line numbers
                existing_codes,
                processed_codes,
                processed_ids,
            )

            # Accumulate results
            response.records_inserted += batch_result["inserted"]
            response.records_skipped_duplicate += batch_result["skipped_duplicate"]
            response.records_skipped_error += batch_result["skipped_error"]
            response.errors.extend(batch_result["errors"])

            # Update processed codes for next batch
            processed_ids.update(batch_result["new_ids"])
            processed_codes['icao'].update(batch_result['new_icao_codes'])
            processed_codes['iata'].update(batch_result['new_iata_codes'])
            processed_ids.update(batch_result['new_ids'])

        return response

    def _process_batch(
        self,
        batch_lines: List[str],
        start_line_number: int,
        existing_codes: dict,
        processed_codes: dict,
        processed_ids: Set[int]
    ) -> dict:
        """Process a batch of 500 lines"""
        result = {
            'inserted': 0,
            'skipped_duplicate': 0,
            'skipped_error': 0,
            'errors': [],
            'new_icao_codes': set(),
            'new_iata_codes': set(),
            'new_ids': set()
        }

        airports_to_insert = []

        for i, line in enumerate(batch_lines):
            line_number = start_line_number + i

            try:
                airport_data = self._parse_airport_line(line)
                if not airport_data:
                    result['skipped_error'] += 1
                    result['errors'].append(f"Line {line_number}: No data returned from parser")
                    continue

                airport_id = airport_data.get("id")
                icao_code = airport_data.get("icao_code")
                iata_code = airport_data.get("iata_code")

                # Check for duplicate IDs
                if airport_id in processed_ids:
                    result['skipped_duplicate'] += 1
                    result['errors'].append(f"Line {line_number}: Duplicate airport ID {airport_id}")
                    continue

                # Check for duplicate codes using new logic
                is_duplicate, duplicate_reason = self._is_duplicate_airport(
                    icao_code, iata_code, existing_codes, processed_codes
                )

                if is_duplicate:
                    result['skipped_duplicate'] += 1
                    result['errors'].append(f"Line {line_number}: {duplicate_reason} for airport {airport_id}")
                    continue

                # Create airport instance
                airport = Airport(**airport_data)

                # Validate airport using model validation
                is_valid, validation_errors = airport.is_valid()
                if not is_valid:
                    result['skipped_error'] += 1
                    result['errors'].extend(validation_errors)
                    continue

                airports_to_insert.append(airport)

                # Track processed codes and IDs
                result['new_ids'].add(airport_id)
                if icao_code:
                    result['new_icao_codes'].add(icao_code)
                if iata_code:
                    result['new_iata_codes'].add(iata_code)

            except Exception as e:
                # Extract airport_id if possible for better error reporting
                try:
                    parts = line.split(",")
                    airport_id = int(parts[0]) if parts else "unknown"
                except:
                    airport_id = "unknown"

                result['skipped_error'] += 1
                result['errors'].append(f"Line {line_number}: Error parsing airport {airport_id} - {str(e)}")
                continue

        # Bulk insert the batch
        if airports_to_insert:
            try:
                self.db.add_all(airports_to_insert)
                self.db.commit()
                result['inserted'] = len(airports_to_insert)

            except IntegrityError:
                self.db.rollback()
                # Get IDs of airports that failed to insert
                failed_ids = [airport.id for airport in airports_to_insert]
                result['skipped_error'] += len(airports_to_insert)
                result['inserted'] = 0
                result['errors'].append(f"Database constraint violation for airports: {failed_ids}")

            except Exception:
                self.db.rollback()
                # Get IDs of airports that failed to insert
                failed_ids = [airport.id for airport in airports_to_insert]
                result['skipped_error'] += len(airports_to_insert)
                result['inserted'] = 0
                result['errors'].append(f"Database error for airports: {failed_ids}")

        return result

    def _get_existing_airport_codes(self) -> dict:
        """Get set of existing airport ICAO codes to check for duplicates"""
        icao_codes = (
            self.db.query(Airport.icao_code)
            .filter(Airport.icao_code.isnot(None), Airport.icao_code != "")
            .all()
        )

        # Get IATA codes
        iata_codes = (
            self.db.query(Airport.iata_code)
            .filter(Airport.iata_code.isnot(None), Airport.iata_code != "")
            .all()
        )

        return {
            "icao": {code[0] for code in icao_codes},
            "iata": {code[0] for code in iata_codes},
        }

    def _parse_airport_line(self, line: str) -> dict:
        """Parse a single line from the airport .dat file"""
        parts = [part.strip() for part in line.split(",")]

        if len(parts) < 11:
            raise ValueError("Insufficient columns - expected at least 11 columns")

        try:
            airport_id = int(parts[0])
        except (ValueError, IndexError):
            raise ValueError("Invalid airport ID")

        name = parts[1].strip('"').strip()
        city = parts[2].strip('"').strip()
        country = parts[3].strip('"').strip()

        if not all([name, city, country]):
            raise ValueError("Missing required fields: name, city, or country")

        if len(parts) >= 12:
            # 12 columns: has both IATA and ICAO codes
            iata_code = (
                parts[4].strip('"').strip() if parts[4] not in ["\\N", ""] else None
            )
            icao_code = (
                parts[5].strip('"').strip() if parts[5] not in ["\\N", ""] else None
            )
            lat_idx, lon_idx, alt_idx, utc_idx, cont_idx, tz_idx = 6, 7, 8, 9, 10, 11
        else:
            # 11 columns: only one airport code (assume it's ICAO)
            icao_code = (
                parts[4].strip('"').strip() if parts[4] not in ["\\N", ""] else None
            )
            iata_code = None
            lat_idx, lon_idx, alt_idx, utc_idx, cont_idx, tz_idx = 5, 6, 7, 8, 9, 10

        # Coordinates and altitude
        try:
            latitude = float(parts[lat_idx]) if parts[lat_idx] != "\\N" else None
        except (ValueError, IndexError):
            latitude = None

        try:
            longitude = float(parts[lon_idx]) if parts[lon_idx] != "\\N" else None
        except (ValueError, IndexError):
            longitude = None

        try:
            altitude = int(float(parts[alt_idx])) if parts[alt_idx] != "\\N" else None
        except (ValueError, IndexError):
            altitude = None

        # Additional fields
        try:
            utc_offset = (
                float(parts[utc_idx])
                if len(parts) > utc_idx and parts[utc_idx] != "\\N"
                else None
            )
        except (ValueError, IndexError):
            utc_offset = None

        continent_code = (
            parts[cont_idx].strip('"').strip()
            if len(parts) > cont_idx and parts[cont_idx] not in ["\\N", ""]
            else None
        )
        timezone = (
            parts[tz_idx].strip('"').strip()
            if len(parts) > tz_idx and parts[tz_idx] not in ["\\N", ""]
            else None
        )

        return {
            "id": airport_id,
            "name": name,
            "city": city,
            "country": country,
            "iata_code": iata_code,
            "icao_code": icao_code,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "utc_offset": utc_offset,
            "continent_code": continent_code,
            "timezone": timezone,
        }

    def _is_duplicate_airport(self, icao_code: str, iata_code: str, existing_codes: dict, processed_codes: dict):
        """
        Check if airport is duplicate based on ICAO or IATA codes
        Returns: (is_duplicate, reason)
        """
        # Priority 1: Check ICAO code if exists
        if icao_code:
            if icao_code in existing_codes['icao'] or icao_code in processed_codes['icao']:
                return True, f"Duplicate ICAO code '{icao_code}'"

        # Priority 2: Check IATA code if ICAO doesn't exist
        elif iata_code:
            if iata_code in existing_codes['iata'] or iata_code in processed_codes['iata']:
                return True, f"Duplicate IATA code '{iata_code}'"

        return False, ""
