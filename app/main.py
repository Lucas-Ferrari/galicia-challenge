from fastapi import FastAPI
from app.config import settings


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Galicia API is running",
        "version": settings.api_version,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "Alive"}
