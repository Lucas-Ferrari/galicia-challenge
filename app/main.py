from fastapi import FastAPI
from app.config import settings

from app.middleware.audit import AuditMiddleware

from app.routes.airports import router as airports_router
from app.routes.routes import router as routes_router
from app.routes.airlines import router as airlines_router


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middlewares
app.add_middleware(AuditMiddleware)


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

# Routers
app.include_router(airports_router)
app.include_router(routes_router)
app.include_router(airlines_router)
