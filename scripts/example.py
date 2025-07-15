"""
Example usage of the Mindat Scraper API.
"""

import sys
from pathlib import Path
import requests
import json
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test API connection."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure it's running.")
        return False

def search_minerals(search_term: str) -> List[Dict[str, Any]]:
    """
    Search for minerals using the API.
    
    Args:
        search_term: Term to search for
        
    Returns:
        List of mineral data
    """
    try:
        payload = {
            "search_term": search_term,
            "save_to_db": True
        }
        
        response = requests.post(f"{BASE_URL}/search", json=payload)
        
        if response.status_code == 200:
            minerals = response.json()
            print(f"✅ Found {len(minerals)} minerals")
            return minerals
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            return []
            
    except Exception as e:
        print(f"❌ Error searching: {str(e)}")
        return []

def get_mineral(mineral_code: str) -> Dict[str, Any]:
    """
    Get mineral by code.
    
    Args:
        mineral_code: Unique mineral identifier
        
    Returns:
        Mineral data or None
    """
    try:
        response = requests.get(f"{BASE_URL}/mineral/{mineral_code}")
        
        if response.status_code == 200:
            mineral = response.json()
            print(f"✅ Retrieved mineral: {mineral['name']}")
            return mineral
        elif response.status_code == 404:
            print(f"❌ Mineral {mineral_code} not found")
            return None
        else:
            print(f"❌ Error retrieving mineral: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error retrieving mineral: {str(e)}")
        return None

def get_all_minerals() -> List[Dict[str, Any]]:
    """
    Get all minerals from database.
    
    Returns:
        List of all mineral data
    """
    try:
        response = requests.get(f"{BASE_URL}/minerals")
        
        if response.status_code == 200:
            minerals = response.json()
            print(f"✅ Retrieved {len(minerals)} minerals from database")
            return minerals
        else:
            print(f"❌ Error retrieving minerals: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error retrieving minerals: {str(e)}")
        return []

def main():
    """Main example function."""
    print("Mindat Scraper API Example")
    print("=" * 40)
    
    # Test API connection
    if not test_api_connection():
        print("Please make sure the API is running with: python -m uvicorn app.api.main:app --reload")
        return
    
    # Example 1: Search for minerals
    print("\n1. Searching for 'quartz' minerals...")
    minerals = search_minerals("quartz")
    
    if minerals:
        print(f"\nFirst result:")
        mineral = minerals[0]
        print(f"Code: {mineral['mineral_code']}")
        print(f"Name: {mineral['name']}")
        print(f"Description: {mineral['description'][:100]}...")
        
        # Example 2: Get specific mineral
        print(f"\n2. Getting mineral by code: {mineral['mineral_code']}")
        retrieved = get_mineral(mineral['mineral_code'])
        
        if retrieved:
            print(f"Retrieved: {retrieved['name']}")
    
    # Example 3: Get all minerals
    print("\n3. Getting all minerals from database...")
    all_minerals = get_all_minerals()
    
    if all_minerals:
        print("Minerals in database:")
        for mineral in all_minerals[:5]:  # Show first 5
            print(f"  - {mineral['name']} (Code: {mineral['mineral_code']})")
        
        if len(all_minerals) > 5:
            print(f"  ... and {len(all_minerals) - 5} more")
    
    print("\n✅ Example completed!")

if __name__ == "__main__":
    main()
