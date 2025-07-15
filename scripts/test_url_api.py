#!/usr/bin/env python3
"""
Test API client for the new URL scraping functionality.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

async def test_url_scraping(url: str, save_to_db: bool = True) -> Dict[str, Any]:
    """
    Test the URL scraping API endpoint.
    
    Args:
        url: Mindat.org URL to scrape
        save_to_db: Whether to save to database
        
    Returns:
        API response data
    """
    api_url = "http://localhost:8000/scrape-url"
    
    payload = {
        "url": url,
        "save_to_db": save_to_db
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                else:
                    error_data = await response.json()
                    return {"success": False, "error": error_data, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

async def test_get_mineral(mineral_code: str) -> Dict[str, Any]:
    """
    Test getting mineral data by code.
    
    Args:
        mineral_code: Mineral code to retrieve
        
    Returns:
        API response data
    """
    api_url = f"http://localhost:8000/mineral/{mineral_code}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                else:
                    error_data = await response.json()
                    return {"success": False, "error": error_data, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

async def main():
    """Main test function."""
    if len(sys.argv) != 2:
        print("Usage: python test_url_api.py <mindat_url>")
        print("Example: python test_url_api.py https://www.mindat.org/min-1720.html")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print("=" * 80)
    print("API URL SCRAPING TEST")
    print("=" * 80)
    print(f"🌐 Testing URL: {url}")
    print("=" * 80)
    
    # Test URL scraping
    print("\n🔍 Testing URL scraping endpoint...")
    scrape_result = await test_url_scraping(url, save_to_db=True)
    
    if scrape_result["success"]:
        print("✅ URL scraping successful!")
        mineral_data = scrape_result["data"]
        
        print(f"\n📊 Scraped Data:")
        print(f"🏷️  Name: {mineral_data.get('name', 'Unknown')}")
        print(f"🔢 Code: {mineral_data.get('mineral_code', 'Unknown')}")
        print(f"📝 Description: {mineral_data.get('description', 'No description')}")
        print(f"📍 Location: {mineral_data.get('location', 'No location')}")
        
        # Show properties count
        properties = mineral_data.get('properties', {})
        print(f"🧪 Properties: {len(properties)} found")
        
        # Show localities count
        localities = mineral_data.get('localities', [])
        print(f"🌍 Localities: {len(localities)} found")
        
        # Show images count
        images = mineral_data.get('images', [])
        print(f"🖼️ Images: {len(images)} found")
        
        # Test retrieving the mineral from database
        mineral_code = mineral_data.get('mineral_code')
        if mineral_code:
            print(f"\n🔍 Testing mineral retrieval by code: {mineral_code}")
            get_result = await test_get_mineral(mineral_code)
            
            if get_result["success"]:
                print("✅ Mineral retrieval successful!")
                retrieved_data = get_result["data"]
                print(f"📊 Retrieved: {retrieved_data.get('name', 'Unknown')}")
            else:
                print("❌ Mineral retrieval failed!")
                print(f"Error: {get_result.get('error', 'Unknown error')}")
        
        # Save results to file
        output_file = f"api_test_result_{mineral_code}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mineral_data, f, indent=2, ensure_ascii=False)
        print(f"\n📁 Results saved to: {output_file}")
        
    else:
        print("❌ URL scraping failed!")
        print(f"Status: {scrape_result.get('status', 'Unknown')}")
        print(f"Error: {scrape_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
