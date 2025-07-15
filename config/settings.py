"""
Configuration settings for the application.
"""

import os
from typing import Optional

class Settings:
    """Application settings."""
    
    # Database settings
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/minerals.json")
    
    # Scraper settings
    SCRAPER_HEADLESS: bool = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "10"))
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Mindat.org settings
    MINDAT_BASE_URL: str = "https://www.mindat.org"
    SEARCH_INPUT_ID: str = "searchboxhp"
    
    # Rate limiting
    RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

# Global settings instance
settings = Settings()
