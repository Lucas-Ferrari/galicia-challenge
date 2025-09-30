from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.airports import AirportService
from app.schemas.airport import AirportImportResponse

router = APIRouter(prefix="/airports", tags=["airports"])

@router.post("/import",
             description="Import airports from a .dat file",
             response_model=AirportImportResponse)
async def import_airports(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Imports airports in batches from a .dat file.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.endswith((".dat", ".csv", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Expected .dat, .csv, or .txt file",
        )

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        file_content = content.decode("utf-8")

        airport_service = AirportService(db)

        result = airport_service.import_airports_from_file_content(
            file_content=file_content,
            filename=file.filename,
        )

        return result

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Unable to decode file. Please ensure it's a valid text file with UTF-8 encoding."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {file.filename}"
            )
