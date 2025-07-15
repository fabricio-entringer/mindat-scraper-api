"""
Quick test script to add sample data and test the API.
"""

import sys
import requests
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import DatabaseService
from config import settings

def add_sample_data():
    """Add sample mineral data to the database."""
    print("Adding sample data to database...")
    
    db = DatabaseService(settings.DATABASE_PATH)
    
    sample_minerals = [
        {
            'mineral_code': '123',
            'name': 'Quartz',
            'description': 'Silicon dioxide (SiO2) is one of the most common minerals in the Earth\'s crust.',
            'location': 'Found worldwide',
            'url': 'https://www.mindat.org/min-123.html',
            'search_term': 'quartz',
            'scraped_at': 1642694400.0
        },
        {
            'mineral_code': '456',
            'name': 'Pyrite',
            'description': 'Iron sulfide (FeS2), also known as "fool\'s gold".',
            'location': 'Found in sedimentary, metamorphic, and igneous rocks',
            'url': 'https://www.mindat.org/min-456.html',
            'search_term': 'pyrite',
            'scraped_at': 1642694400.0
        },
        {
            'mineral_code': '789',
            'name': 'Calcite',
            'description': 'Calcium carbonate (CaCO3) is a common mineral found in limestone and marble.',
            'location': 'Found in sedimentary rocks worldwide',
            'url': 'https://www.mindat.org/min-789.html',
            'search_term': 'calcite',
            'scraped_at': 1642694400.0
        }
    ]
    
    for mineral in sample_minerals:
        success = db.save_mineral(mineral)
        if success:
            print(f"✅ Added {mineral['name']} (Code: {mineral['mineral_code']})")
        else:
            print(f"❌ Failed to add {mineral['name']}")
    
    db.close()
    print(f"Sample data added successfully!")

def test_api_endpoints():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    print("\nTesting API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False
    
    # Test get all minerals
    try:
        response = requests.get(f"{base_url}/minerals")
        if response.status_code == 200:
            minerals = response.json()
            print(f"✅ Found {len(minerals)} minerals in database")
            for mineral in minerals:
                print(f"   - {mineral['name']} (Code: {mineral['mineral_code']})")
        else:
            print(f"❌ Get minerals failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting minerals: {e}")
    
    # Test get specific mineral
    try:
        response = requests.get(f"{base_url}/mineral/123")
        if response.status_code == 200:
            mineral = response.json()
            print(f"✅ Retrieved mineral: {mineral['name']}")
        else:
            print(f"❌ Get specific mineral failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting specific mineral: {e}")
    
    # Test search endpoint
    try:
        response = requests.get(f"{base_url}/search/quartz")
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Search returned {len(results)} results")
        else:
            print(f"❌ Search failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error during search: {e}")
    
    return True

def main():
    """Main function."""
    print("Mindat Scraper API Test")
    print("=" * 40)
    
    # Add sample data
    add_sample_data()
    
    # Test API endpoints
    if test_api_endpoints():
        print("\n✅ API test completed successfully!")
        print("\nYou can now:")
        print("- Visit http://localhost:8000/docs for API documentation")
        print("- Test endpoints manually with curl or Postman")
        print("- Use the scripts/example.py script for more detailed testing")
    else:
        print("\n❌ API test failed. Make sure the server is running.")

if __name__ == "__main__":
    main()
