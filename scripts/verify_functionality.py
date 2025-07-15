#!/usr/bin/env python3
"""
Verification script to demonstrate the complete URL scraping functionality.
"""

import requests
import json
import time
from typing import Dict, Any

def test_api_endpoint(url: str) -> Dict[str, Any]:
    """Test the API endpoint."""
    api_url = "http://localhost:8000/scrape-url"
    
    payload = {
        "url": url,
        "save_to_db": True
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.json(), "status": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e), "status": None}

def test_get_mineral(mineral_code: str) -> Dict[str, Any]:
    """Test getting mineral from database."""
    api_url = f"http://localhost:8000/mineral/{mineral_code}"
    
    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.json(), "status": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e), "status": None}

def main():
    """Main verification function."""
    print("=" * 80)
    print("MINDAT URL SCRAPING FUNCTIONALITY VERIFICATION")
    print("=" * 80)
    
    # Test URLs
    test_urls = [
        "https://www.mindat.org/min-1720.html",  # Gold
        "https://www.mindat.org/min-2549.html",  # Quartz
        "https://www.mindat.org/min-3224.html",  # Pyrite
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}: Testing URL {url}")
        print("-" * 60)
        
        # Test API scraping
        result = test_api_endpoint(url)
        
        if result["success"]:
            data = result["data"]
            print(f"✅ Successfully scraped: {data.get('name', 'Unknown')}")
            print(f"   📝 Description: {data.get('description', 'No description')[:100]}...")
            print(f"   📍 Location: {data.get('location', 'No location')[:100]}...")
            print(f"   🧪 Properties: {len(data.get('properties', {}))} found")
            print(f"   🌍 Localities: {len(data.get('localities', []))} found")
            print(f"   🖼️ Images: {len(data.get('images', []))} found")
            
            # Test retrieval from database
            mineral_code = data.get('mineral_code')
            if mineral_code:
                print(f"   🔍 Testing database retrieval for code: {mineral_code}")
                get_result = test_get_mineral(mineral_code)
                
                if get_result["success"]:
                    retrieved_data = get_result["data"]
                    print(f"   ✅ Retrieved from database: {retrieved_data.get('name', 'Unknown')}")
                else:
                    print(f"   ❌ Failed to retrieve from database: {get_result.get('error', 'Unknown error')}")
            
        else:
            print(f"❌ Failed to scrape: {result.get('error', 'Unknown error')}")
        
        # Add delay between tests
        if i < len(test_urls):
            print("   ⏳ Waiting 10 seconds before next test...")
            time.sleep(10)
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    
    # Test health endpoint
    print("\n🏥 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check: {health_data.get('status', 'Unknown')}")
            print(f"   Database: {health_data.get('database', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test get all minerals
    print("\n📋 Testing get all minerals endpoint...")
    try:
        response = requests.get("http://localhost:8000/minerals", timeout=10)
        if response.status_code == 200:
            minerals = response.json()
            print(f"✅ Found {len(minerals)} minerals in database")
            for mineral in minerals[:3]:  # Show first 3
                print(f"   - {mineral.get('name', 'Unknown')} (Code: {mineral.get('mineral_code', 'Unknown')})")
        else:
            print(f"❌ Get all minerals failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get all minerals error: {e}")

if __name__ == "__main__":
    main()
