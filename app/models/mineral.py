"""
Pydantic models for the Mindat Scraper API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
import time
import re

class MineralBase(BaseModel):
    """Base mineral model."""
    mineral_code: str = Field(..., description="Unique identifier for the mineral")
    name: str = Field(..., description="Name of the mineral")
    description: str = Field(..., description="Description of the mineral")
    location: str = Field(..., description="Location where the mineral is found")
    url: str = Field(..., description="URL to the mineral's page on mindat.org")
    search_term: str = Field(..., description="Search term used to find this mineral")
    scraped_at: float = Field(default_factory=time.time, description="Timestamp when data was scraped")
    properties: Optional[Dict[str, str]] = Field(default_factory=dict, description="Chemical and physical properties")
    localities: Optional[List[str]] = Field(default_factory=list, description="List of localities where mineral is found")
    images: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="List of mineral images")
    introduction: Optional[str] = Field(None, description="Introduction text about the mineral")

class MineralCreate(MineralBase):
    """Model for creating a new mineral."""
    pass

class MineralUpdate(BaseModel):
    """Model for updating mineral data."""
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    search_term: Optional[str] = None
    properties: Optional[Dict[str, str]] = None
    localities: Optional[List[str]] = None
    images: Optional[List[Dict[str, str]]] = None
    introduction: Optional[str] = None

class MineralResponse(MineralBase):
    """Response model for mineral data."""
    pass

class SearchRequest(BaseModel):
    """Request model for search operations."""
    search_term: str = Field(..., description="Term to search for")
    save_to_db: bool = Field(default=True, description="Whether to save results to database")

class SearchByNameRequest(BaseModel):
    """Request model for searching by mineral name."""
    name: str = Field(..., description="Name of the mineral to search for")

class SearchByNameResponse(BaseModel):
    """Response model for name-based search."""
    results: List[MineralResponse] = Field(default_factory=list, description="List of minerals found")
    total_found: int = Field(..., description="Total number of minerals found")

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    database: str = Field(..., description="Database connection status")

class URLScrapeRequest(BaseModel):
    """Request model for URL scraping operations."""
    url: str = Field(..., description="Direct URL to mineral page on mindat.org")
    save_to_db: bool = Field(default=True, description="Whether to save result to database")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate that the URL is a valid mindat.org mineral page."""
        if not v.startswith('https://www.mindat.org/min-'):
            raise ValueError('URL must be a mindat.org mineral page (format: https://www.mindat.org/min-XXXX.html)')
        if not v.endswith('.html'):
            raise ValueError('URL must end with .html')
        if not re.match(r'https://www\.mindat\.org/min-\d+\.html', v):
            raise ValueError('URL must follow the pattern: https://www.mindat.org/min-[number].html')
        return v

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")

class APIInfoResponse(BaseModel):
    """API information response model."""
    message: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    endpoints: dict = Field(..., description="Available endpoints")
