"""
API routes for mineral operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging
import time

from app.models import (
    MineralResponse, 
    SearchRequest, 
    SearchByNameRequest,
    SearchByNameResponse,
    URLScrapeRequest,
    ErrorResponse
)
from app.services import DatabaseService, ScraperService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
db_service = DatabaseService()
scraper_service = ScraperService(headless=True)

@router.get("/mineral/{mineral_code}", response_model=MineralResponse)
async def get_mineral(mineral_code: str):
    """
    Get mineral data by code.
    
    Args:
        mineral_code: Unique identifier for the mineral
        
    Returns:
        Mineral data if found
        
    Raises:
        HTTPException: 404 if mineral not found
    """
    try:
        mineral_data = db_service.get_mineral(mineral_code)
        
        if not mineral_data:
            raise HTTPException(
                status_code=404,
                detail=f"Mineral with code '{mineral_code}' not found"
            )
        
        return MineralResponse(**mineral_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mineral {mineral_code}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/minerals", response_model=List[MineralResponse])
async def get_all_minerals():
    """
    Get all minerals from the database.
    
    Returns:
        List of all mineral records
    """
    try:
        minerals = db_service.get_all_minerals()
        return [MineralResponse(**mineral) for mineral in minerals]
        
    except Exception as e:
        logger.error(f"Error retrieving all minerals: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.post("/scrape-url", response_model=MineralResponse)
async def scrape_mineral_from_url(request: URLScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape mineral data from a specific mindat.org URL.
    
    Args:
        request: URL scrape request containing URL and save_to_db flag
        background_tasks: FastAPI background tasks
        
    Returns:
        Scraped mineral data
        
    Raises:
        HTTPException: 400 for invalid URL, 404 if mineral not found, 500 for server errors
    """
    try:
        scraper = ScraperService(headless=True)
        mineral_data = scraper.scrape_mineral_from_url(request.url)
        
        if not mineral_data:
            raise HTTPException(
                status_code=404,
                detail=f"Could not scrape mineral data from URL: {request.url}"
            )
        
        # Validate that we got essential data
        if not mineral_data.get('name') or mineral_data.get('name') == 'Unknown':
            raise HTTPException(
                status_code=404,
                detail=f"Mineral page not found or inaccessible at URL: {request.url}"
            )
        
        if request.save_to_db:
            # Save mineral to database in background
            background_tasks.add_task(save_mineral_to_db, mineral_data)
        
        return MineralResponse(**mineral_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping mineral from URL {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping mineral from URL: {str(e)}"
        )

@router.post("/search", response_model=List[MineralResponse])
async def search_minerals(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Search for minerals and optionally save to database.
    
    Args:
        request: Search request containing search_term and save_to_db flag
        background_tasks: FastAPI background tasks
        
    Returns:
        List of found minerals
    """
    try:
        scraper = ScraperService(headless=True)
        minerals = scraper.search_mineral(request.search_term)
        
        if request.save_to_db and minerals:
            # Save minerals to database in background
            background_tasks.add_task(save_minerals_to_db, minerals)
        
        return [MineralResponse(**mineral) for mineral in minerals]
        
    except Exception as e:
        logger.error(f"Error searching minerals: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for minerals: {str(e)}"
        )

@router.delete("/mineral/{mineral_code}")
async def delete_mineral(mineral_code: str):
    """
    Delete a mineral from the database.
    
    Args:
        mineral_code: Unique identifier for the mineral
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if mineral not found
    """
    try:
        success = db_service.delete_mineral(mineral_code)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Mineral with code '{mineral_code}' not found"
            )
        
        return {"message": f"Mineral '{mineral_code}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mineral {mineral_code}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/search/{query}", response_model=List[MineralResponse])
async def search_database(query: str):
    """
    Search minerals in the database by name or description.
    
    Args:
        query: Search query string
        
    Returns:
        List of matching mineral records
    """
    try:
        minerals = db_service.search_minerals(query)
        return [MineralResponse(**mineral) for mineral in minerals]
        
    except Exception as e:
        logger.error(f"Error searching database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.post("/search-by-name", response_model=SearchByNameResponse)
async def search_by_name(request: SearchByNameRequest, background_tasks: BackgroundTasks):
    """
    Search for minerals by name.
    
    Searches both the local database and online sources to find minerals 
    matching the provided name. Returns all matching results as JSON.
    
    Args:
        request: Search request containing the mineral name
        background_tasks: FastAPI background tasks for saving results
        
    Returns:
        SearchByNameResponse containing all matching minerals
    """
    try:
        all_results = []
        
        # Search in local database first
        logger.info(f"Searching for mineral name: {request.name}")
        db_results = db_service.search_minerals_by_partial_name(request.name)
        
        if db_results:
            all_results.extend([MineralResponse(**mineral) for mineral in db_results])
            logger.info(f"Found {len(db_results)} minerals in database")
        
        # Search online if not found in database or if we want more results
        if not db_results or len(db_results) < 5:  # Get more results if we have less than 5
            logger.info(f"Searching online for mineral name: {request.name}")
            
            try:
                scraper = ScraperService(headless=True)
                online_results = scraper.search_mineral(request.name)
                
                if online_results:
                    # Filter out results that are already in our results
                    existing_codes = {m.mineral_code for m in all_results}
                    new_results = [
                        mineral for mineral in online_results 
                        if mineral.get('mineral_code') not in existing_codes
                    ]
                    
                    if new_results:
                        all_results.extend([MineralResponse(**mineral) for mineral in new_results])
                        logger.info(f"Found {len(new_results)} new minerals online")
                        
                        # Save to database in background
                        background_tasks.add_task(save_minerals_to_db, new_results)
                
            except Exception as e:
                logger.error(f"Error searching online: {str(e)}")
                # Continue with database results if online search fails
        
        return SearchByNameResponse(
            results=all_results,
            total_found=len(all_results)
        )
        
    except Exception as e:
        logger.error(f"Error in search by name: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for mineral by name: {str(e)}"
        )

@router.get("/name/{name}", response_model=MineralResponse)
async def get_mineral_by_name(name: str):
    """
    Get mineral by exact name match from database.
    
    Args:
        name: Exact name of the mineral
        
    Returns:
        Mineral data if found
        
    Raises:
        HTTPException: 404 if mineral not found
    """
    try:
        mineral_data = db_service.get_mineral_by_name(name)
        
        if not mineral_data:
            raise HTTPException(
                status_code=404,
                detail=f"Mineral with name '{name}' not found"
            )
        
        return MineralResponse(**mineral_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mineral by name {name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/search-name/{name}", response_model=List[MineralResponse])
async def search_by_name_get(name: str):
    """
    Search for minerals by name using GET request.
    
    Simple endpoint that searches for minerals by name and returns
    the results as a JSON list. Searches both database and online.
    
    Args:
        name: Name of the mineral to search for
        
    Returns:
        List of matching minerals
    """
    try:
        all_results = []
        
        # Search in local database first
        logger.info(f"Searching for mineral name: {name}")
        db_results = db_service.search_minerals_by_partial_name(name)
        
        if db_results:
            all_results.extend([MineralResponse(**mineral) for mineral in db_results])
            logger.info(f"Found {len(db_results)} minerals in database")
        
        # Search online if not found in database or if we want more results
        if not db_results or len(db_results) < 5:  # Get more results if we have less than 5
            logger.info(f"Searching online for mineral name: {name}")
            
            try:
                scraper = ScraperService(headless=True)
                online_results = scraper.search_mineral(name)
                
                if online_results:
                    # Filter out results that are already in our results
                    existing_codes = {m.mineral_code for m in all_results}
                    new_results = [
                        mineral for mineral in online_results 
                        if mineral.get('mineral_code') not in existing_codes
                    ]
                    
                    if new_results:
                        all_results.extend([MineralResponse(**mineral) for mineral in new_results])
                        logger.info(f"Found {len(new_results)} new minerals online")
                        
                        # Save to database (no background task needed for GET)
                        try:
                            for mineral in new_results:
                                db_service.save_mineral(mineral)
                        except:
                            pass  # Ignore save errors for GET request
                
            except Exception as e:
                logger.error(f"Error searching online: {str(e)}")
                # Continue with database results if online search fails
        
        return all_results
        
    except Exception as e:
        logger.error(f"Error in search by name: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for mineral by name: {str(e)}"
        )

def save_mineral_to_db(mineral_data: dict):
    """
    Background task to save a single mineral to database.
    
    Args:
        mineral_data: Dictionary containing mineral data
    """
    try:
        success = db_service.save_mineral(mineral_data)
        if success:
            logger.info(f"Saved mineral {mineral_data.get('mineral_code', 'Unknown')} to database")
        else:
            logger.error(f"Failed to save mineral {mineral_data.get('mineral_code', 'Unknown')} to database")
    except Exception as e:
        logger.error(f"Error saving mineral to database: {str(e)}")

def save_minerals_to_db(minerals: List[dict]):
    """
    Background task to save minerals to database.
    
    Args:
        minerals: List of mineral data dictionaries
    """
    try:
        for mineral in minerals:
            db_service.save_mineral(mineral)
        logger.info(f"Saved {len(minerals)} minerals to database")
    except Exception as e:
        logger.error(f"Error saving minerals to database: {str(e)}")
