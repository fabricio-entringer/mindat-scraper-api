"""
Main API application setup.
"""

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging

from app.models import APIInfoResponse, HealthResponse
from app.services import DatabaseService
from app.core import setup_logging
from config import settings
from .minerals import router as minerals_router

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize database service
db_service = DatabaseService(settings.DATABASE_PATH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting up Mindat Scraper API...")
    yield
    logger.info("Shutting down Mindat Scraper API...")
    db_service.close()

app = FastAPI(
    title="Mindat Scraper API",
    description="API for scraping and retrieving mineral data from mindat.org",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(minerals_router, tags=["minerals"])

@app.get("/", response_model=APIInfoResponse)
async def root():
    """Root endpoint with API information."""
    return APIInfoResponse(
        message="Mindat Scraper API",
        version="1.0.0",
        endpoints={
            "search": "/search",
            "scrape-url": "/scrape-url",
            "mineral": "/mineral/{mineral_code}",
            "minerals": "/minerals",
            "health": "/health"
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        database="connected"
    )

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return HTTPException(
        status_code=404,
        detail="Resource not found"
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )
