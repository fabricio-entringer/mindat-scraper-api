#!/usr/bin/env python3
"""
Comprehensive test for the URL scraping functionality.
"""

import sys
import os
import logging
import json
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper import ScraperService
from app.services.database import DatabaseService
from app.models.mineral import URLScrapeRequest, MineralResponse

# Set up logging
logging.basicConfig(level=logging.INFO)

class TestURLScraping(unittest.TestCase):
    """Test cases for URL scraping functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_url = "https://www.mindat.org/min-1720.html"
        self.invalid_url = "https://www.invalid.com/min-1720.html"
        self.db_service = DatabaseService(":memory:")  # Use in-memory database for testing
    
    def tearDown(self):
        """Clean up after tests."""
        self.db_service.close()
    
    def test_url_validation(self):
        """Test URL validation in URLScrapeRequest."""
        # Valid URL
        valid_request = URLScrapeRequest(url=self.test_url, save_to_db=False)
        self.assertEqual(valid_request.url, self.test_url)
        
        # Invalid URLs
        invalid_urls = [
            "https://www.invalid.com/min-1720.html",
            "https://www.mindat.org/invalid-1720.html",
            "https://www.mindat.org/min-1720.pdf",
            "not-a-url"
        ]
        
        for invalid_url in invalid_urls:
            with self.assertRaises(Exception):
                URLScrapeRequest(url=invalid_url, save_to_db=False)
    
    def test_mineral_code_extraction(self):
        """Test mineral code extraction from URL."""
        import re
        
        # Test pattern matching
        pattern = r'/min-(\d+)\.html'
        
        test_cases = [
            ("https://www.mindat.org/min-1720.html", "1720"),
            ("https://www.mindat.org/min-123.html", "123"),
            ("https://www.mindat.org/min-9999.html", "9999")
        ]
        
        for url, expected_code in test_cases:
            match = re.search(pattern, url)
            self.assertIsNotNone(match)
            self.assertEqual(match.group(1), expected_code)
    
    def test_database_operations(self):
        """Test database save and retrieve operations."""
        # Create test mineral data
        mineral_data = {
            'mineral_code': '1720',
            'name': 'Gold',
            'description': 'Native gold mineral',
            'location': 'Worldwide',
            'url': 'https://www.mindat.org/min-1720.html',
            'search_term': 'direct_url_1720',
            'scraped_at': 1234567890,
            'properties': {'Formula': 'Au', 'Hardness': '2.5-3'},
            'localities': ['California', 'Alaska'],
            'images': [{'src': 'test.jpg', 'alt': 'Test image'}],
            'introduction': 'Gold is a precious metal...'
        }
        
        # Test save
        success = self.db_service.save_mineral(mineral_data)
        self.assertTrue(success)
        
        # Test retrieve
        retrieved = self.db_service.get_mineral('1720')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['name'], 'Gold')
        self.assertEqual(retrieved['mineral_code'], '1720')
        
        # Test update
        mineral_data['name'] = 'Updated Gold'
        success = self.db_service.save_mineral(mineral_data)
        self.assertTrue(success)
        
        updated = self.db_service.get_mineral('1720')
        self.assertEqual(updated['name'], 'Updated Gold')
    
    def test_mineral_response_model(self):
        """Test MineralResponse model validation."""
        # Valid mineral data
        mineral_data = {
            'mineral_code': '1720',
            'name': 'Gold',
            'description': 'Native gold mineral',
            'location': 'Worldwide',
            'url': 'https://www.mindat.org/min-1720.html',
            'search_term': 'direct_url_1720',
            'scraped_at': 1234567890,
            'properties': {'Formula': 'Au'},
            'localities': ['California'],
            'images': [{'src': 'test.jpg', 'alt': 'Test'}],
            'introduction': 'Gold is precious...'
        }
        
        # Should not raise exception
        response = MineralResponse(**mineral_data)
        self.assertEqual(response.name, 'Gold')
        self.assertEqual(response.mineral_code, '1720')
    
    @patch('app.services.scraper.requests.Session.get')
    def test_scraper_service_init(self, mock_get):
        """Test ScraperService initialization."""
        scraper = ScraperService(headless=True)
        self.assertEqual(scraper.base_url, "https://www.mindat.org")
        self.assertIsNotNone(scraper.session)
        self.assertEqual(scraper.timeout, 30)
    
    def test_property_extraction_logic(self):
        """Test the property extraction logic."""
        from bs4 import BeautifulSoup
        
        # Mock HTML for testing
        html_content = """
        <div id="introdata">
            <div>
                <span>Formula:</span>
                <div>Au</div>
            </div>
            <div>
                <span>Hardness:</span>
                <div>2.5-3</div>
            </div>
        </div>
        <div class="mindatarow">
            <div class="mindatath">Colour:</div>
            <div class="mindatam2">Golden yellow</div>
        </div>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        scraper = ScraperService(headless=True)
        
        # Test property extraction
        properties = scraper._extract_mineral_properties(soup)
        
        # Should extract properties from both sections
        self.assertIn('Formula', properties)
        self.assertIn('Hardness', properties)
        self.assertIn('Colour', properties)
        
        self.assertEqual(properties['Formula'], 'Au')
        self.assertEqual(properties['Hardness'], '2.5-3')
        self.assertEqual(properties['Colour'], 'Golden yellow')
    
    def test_locality_extraction_logic(self):
        """Test locality extraction logic."""
        from bs4 import BeautifulSoup
        
        # Mock HTML with locality links
        html_content = """
        <a href="/loc-1234.html">California</a>
        <a href="/loc-5678.html">Alaska</a>
        <a href="/loc-9999.html">Colorado</a>
        <a href="/other-link.html">Not a locality</a>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        scraper = ScraperService(headless=True)
        
        localities = scraper._extract_localities(soup)
        
        # Should extract only locality links
        self.assertEqual(len(localities), 3)
        self.assertIn('California', localities)
        self.assertIn('Alaska', localities)
        self.assertIn('Colorado', localities)
    
    def test_image_extraction_logic(self):
        """Test image extraction logic."""
        from bs4 import BeautifulSoup
        
        # Mock HTML with images
        html_content = """
        <img src="/images/mineral1.jpg" alt="Gold specimen">
        <img src="/images/mineral2.png" alt="Another gold specimen">
        <img src="/images/star.png" alt="Rating star">
        <img src="/images/logo.gif" alt="Site logo">
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        scraper = ScraperService(headless=True)
        
        images = scraper._extract_mineral_images(soup)
        
        # Should extract only actual mineral images (not stars, logos, etc.)
        self.assertEqual(len(images), 2)
        self.assertTrue(all('mindat.org' in img['src'] for img in images))
    
    @patch('app.services.scraper.requests.Session.get')
    def test_error_handling(self, mock_get):
        """Test error handling in scraping methods."""
        # Mock requests to raise an exception
        mock_get.side_effect = Exception("Network error")
        
        scraper = ScraperService(headless=True)
        
        # Test with invalid URL
        result = scraper.scrape_mineral_from_url("invalid-url")
        self.assertIsNone(result)
        
        # Test with non-mindat URL
        result = scraper.scrape_mineral_from_url("https://www.example.com/test.html")
        self.assertIsNone(result)

def run_tests():
    """Run all tests."""
    print("=" * 80)
    print("RUNNING URL SCRAPING TESTS")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestURLScraping)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    if result.errors:
        print("\nErrors:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    print("=" * 80)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
