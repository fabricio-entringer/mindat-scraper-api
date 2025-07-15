"""
CLI utility for testing the scraper manually.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import ScraperService, DatabaseService
from app.core import setup_logging
from config import settings
import json

def scrape_and_save(search_term: str, headless: bool = True):
    """
    Scrape minerals and save to database.
    
    Args:
        search_term: Term to search for
        headless: Whether to run browser in headless mode
    """
    try:
        # Setup logging
        setup_logging(settings.LOG_LEVEL)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting scrape for: {search_term}")
        
        # Initialize scraper
        scraper = ScraperService(headless=headless)
        
        # Search for minerals
        minerals = scraper.search_mineral(search_term)
        
        if not minerals:
            logger.warning("No minerals found")
            return
        
        # Initialize database
        db = DatabaseService(settings.DATABASE_PATH)
        
        # Save minerals to database
        saved_count = 0
        for mineral in minerals:
            if db.save_mineral(mineral):
                saved_count += 1
        
        logger.info(f"Saved {saved_count} minerals to database")
        
        # Print results
        print(f"\nFound {len(minerals)} minerals:")
        print("-" * 50)
        
        for mineral in minerals:
            print(f"Code: {mineral['mineral_code']}")
            print(f"Name: {mineral['name']}")
            print(f"Description: {mineral['description'][:100]}...")
            print(f"URL: {mineral['url']}")
            print("-" * 50)
        
        # Close connections
        scraper.close()
        db.close()
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='Mindat Scraper CLI')
    parser.add_argument('search_term', help='Term to search for')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run browser in headless mode (default: True)')
    parser.add_argument('--show-browser', action='store_true',
                        help='Show browser window (sets headless=False)')
    
    args = parser.parse_args()
    
    # Determine headless mode
    headless = args.headless and not args.show_browser
    
    scrape_and_save(args.search_term, headless)

if __name__ == "__main__":
    main()
