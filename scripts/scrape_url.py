#!/usr/bin/env python3
"""
CLI script to test URL scraping functionality.
"""

import sys
import os
import logging
import json
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper import ScraperService
from app.services.database import DatabaseService
from app.models.mineral import URLScrapeRequest

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main function to test URL scraping."""
    if len(sys.argv) != 2:
        print("Usage: python scrape_url.py <mindat_url>")
        print("Example: python scrape_url.py https://www.mindat.org/min-1720.html")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Validate URL format
    try:
        URLScrapeRequest(url=url, save_to_db=False)
    except Exception as e:
        print(f"❌ Invalid URL format: {e}")
        sys.exit(1)
    
    print("=" * 80)
    print("MINDAT URL SCRAPER")
    print("=" * 80)
    print(f"🌐 Scraping URL: {url}")
    print("=" * 80)
    
    # Initialize services
    scraper = ScraperService(headless=False)  # Use visible browser for testing
    db_service = DatabaseService()
    
    try:
        # Scrape the mineral data
        mineral_data = scraper.scrape_mineral_from_url(url)
        
        if not mineral_data:
            print("❌ Failed to scrape mineral data")
            return
        
        print("\n" + "=" * 80)
        print("SCRAPED MINERAL DATA")
        print("=" * 80)
        
        # Display basic info
        print(f"🏷️  Name: {mineral_data.get('name', 'Unknown')}")
        print(f"🔢 Code: {mineral_data.get('mineral_code', 'Unknown')}")
        print(f"📝 Description: {mineral_data.get('description', 'No description')}")
        print(f"📍 Location: {mineral_data.get('location', 'No location')}")
        print(f"🌐 URL: {mineral_data.get('url', 'No URL')}")
        
        # Display properties
        properties = mineral_data.get('properties', {})
        if properties:
            print("\n🧪 Chemical & Physical Properties:")
            for prop, value in properties.items():
                print(f"   • {prop}: {value}")
        
        # Display localities
        localities = mineral_data.get('localities', [])
        if localities:
            print(f"\n🌍 Found {len(localities)} localities:")
            for i, loc in enumerate(localities[:10]):  # Show first 10
                print(f"   {i+1}. {loc}")
        
        # Display images
        images = mineral_data.get('images', [])
        if images:
            print(f"\n🖼️ Found {len(images)} images:")
            for i, img in enumerate(images[:5]):  # Show first 5
                print(f"   {i+1}. {img.get('src', 'No source')} - {img.get('alt', 'No alt text')}")
        
        # Display introduction
        introduction = mineral_data.get('introduction', '')
        if introduction:
            print(f"\n📖 Introduction: {introduction}")
        
        success = db_service.save_mineral(mineral_data)
        if success:
            print("✅ Mineral data saved to database!")
        else:
            print("❌ Failed to save mineral data to database")
        
        # Save to JSON file for inspection
        output_file = f"scraped_mineral_{mineral_data.get('mineral_code', 'unknown')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mineral_data, f, indent=2, ensure_ascii=False)
        print(f"\n📁 Data saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        scraper.close()
        db_service.close()

if __name__ == "__main__":
    main()
