"""
Test suite for the Mindat Scraper API.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from pathlib import Path
import sys
import requests

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import modules to test
from app.services import DatabaseService, ScraperService
from app.models import MineralResponse, SearchRequest

class TestDatabaseService:
    """Test cases for DatabaseService class."""
    
    def setup_method(self):
        """Setup test database."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.db = DatabaseService(self.temp_file.name)
        
    def teardown_method(self):
        """Cleanup test database."""
        self.db.close()
        os.unlink(self.temp_file.name)
    
    def test_save_mineral(self):
        """Test saving mineral data."""
        mineral_data = {
            'mineral_code': 'TEST001',
            'name': 'Test Mineral',
            'description': 'A test mineral',
            'location': 'Test Location',
            'url': 'https://test.com',
            'search_term': 'test',
            'scraped_at': 1234567890.0
        }
        
        result = self.db.save_mineral(mineral_data)
        assert result is True
        
        # Verify mineral was saved
        retrieved = self.db.get_mineral('TEST001')
        assert retrieved is not None
        assert retrieved['name'] == 'Test Mineral'
    
    def test_save_mineral_without_code(self):
        """Test saving mineral without code fails."""
        mineral_data = {
            'name': 'Test Mineral',
            'description': 'A test mineral'
        }
        
        result = self.db.save_mineral(mineral_data)
        assert result is False
    
    def test_get_mineral_not_found(self):
        """Test getting non-existent mineral."""
        result = self.db.get_mineral('NONEXISTENT')
        assert result is None
    
    def test_update_existing_mineral(self):
        """Test updating existing mineral."""
        # Save initial mineral
        mineral_data = {
            'mineral_code': 'TEST001',
            'name': 'Test Mineral',
            'description': 'Initial description'
        }
        self.db.save_mineral(mineral_data)
        
        # Update mineral
        updated_data = {
            'mineral_code': 'TEST001',
            'name': 'Updated Mineral',
            'description': 'Updated description'
        }
        result = self.db.save_mineral(updated_data)
        assert result is True
        
        # Verify update
        retrieved = self.db.get_mineral('TEST001')
        assert retrieved['name'] == 'Updated Mineral'
        assert retrieved['description'] == 'Updated description'
    
    def test_delete_mineral(self):
        """Test deleting mineral."""
        # Save mineral
        mineral_data = {
            'mineral_code': 'TEST001',
            'name': 'Test Mineral',
            'description': 'A test mineral'
        }
        self.db.save_mineral(mineral_data)
        
        # Delete mineral
        result = self.db.delete_mineral('TEST001')
        assert result is True
        
        # Verify deletion
        retrieved = self.db.get_mineral('TEST001')
        assert retrieved is None
    
    def test_delete_nonexistent_mineral(self):
        """Test deleting non-existent mineral."""
        result = self.db.delete_mineral('NONEXISTENT')
        assert result is False
    
    def test_search_minerals(self):
        """Test searching minerals."""
        # Save test minerals
        minerals = [
            {
                'mineral_code': 'TEST001',
                'name': 'Quartz',
                'description': 'Silicon dioxide mineral'
            },
            {
                'mineral_code': 'TEST002',
                'name': 'Feldspar',
                'description': 'Aluminum silicate mineral'
            }
        ]
        
        for mineral in minerals:
            self.db.save_mineral(mineral)
        
        # Search by name
        results = self.db.search_minerals('Quartz')
        assert len(results) == 1
        assert results[0]['name'] == 'Quartz'
        
        # Search by description
        results = self.db.search_minerals('silicate')
        assert len(results) == 1
        assert results[0]['name'] == 'Feldspar'

class TestScraperService:
    """Test cases for ScraperService class."""
    
    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = ScraperService()
        assert scraper.base_url == "https://www.mindat.org"
        assert scraper.session is not None
        assert scraper.timeout == 30
    
    @patch('app.services.scraper.requests.Session.get')
    def test_get_page_success(self, mock_get):
        """Test successful page request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_get.return_value = mock_response
        
        scraper = ScraperService()
        response = scraper._get_page("https://www.mindat.org/min-1720.html")
        
        assert response == mock_response
        mock_get.assert_called_once()
    
    @patch('app.services.scraper.requests.Session.get')
    def test_get_page_failure(self, mock_get):
        """Test failed page request."""
        # Mock failed response
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        scraper = ScraperService()
        response = scraper._get_page("https://www.mindat.org/min-1720.html")
        
        assert response is None
    
    def test_mineral_code_extraction(self):
        """Test mineral code extraction from URL."""
        scraper = ScraperService()
        
        # Test with mock link element
        mock_link = Mock()
        mock_link.get.return_value = '/min-12345.html'
        mock_link.get_text.return_value = 'Test Mineral'
        mock_link.parent = None
        
        result = scraper._extract_mineral_info_from_link(mock_link, 'test')
        
        assert result is not None
        assert result['mineral_code'] == '12345'
        assert result['name'] == 'Test Mineral'
        assert result['url'] == 'https://www.mindat.org/min-12345.html'
    
    @patch('app.services.scraper.ScraperService._get_page')
    def test_scrape_mineral_from_url(self, mock_get_page):
        """Test scraping mineral from URL."""
        # Mock HTML content
        mock_html = '''
        <html>
            <body>
                <h1 class="mineralheading">Gold</h1>
                <div id="introdata">
                    <div><span>Formula:</span><div>Au</div></div>
                </div>
            </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_get_page.return_value = mock_response
        
        scraper = ScraperService()
        result = scraper.scrape_mineral_from_url("https://www.mindat.org/min-1720.html")
        
        assert result is not None
        assert result['mineral_code'] == '1720'
        assert result['name'] == 'Gold'
        assert 'Formula' in result['properties']
        assert result['properties']['Formula'] == 'Au'

class TestModels:
    """Test cases for Pydantic models."""
    
    def test_mineral_response_model(self):
        """Test MineralResponse model."""
        data = {
            'mineral_code': '123',
            'name': 'Test Mineral',
            'description': 'A test mineral',
            'location': 'Test Location',
            'url': 'https://test.com',
            'search_term': 'test',
            'scraped_at': 1234567890.0
        }
        
        mineral = MineralResponse(**data)
        assert mineral.mineral_code == '123'
        assert mineral.name == 'Test Mineral'
    
    def test_search_request_model(self):
        """Test SearchRequest model."""
        data = {
            'search_term': 'quartz',
            'save_to_db': True
        }
        
        request = SearchRequest(**data)
        assert request.search_term == 'quartz'
        assert request.save_to_db is True

def test_api_endpoints():
    """Test API endpoints."""
    # This would require setting up FastAPI test client
    # For now, just verify imports work
    try:
        from app.api import app
        assert app is not None
    except ImportError:
        pytest.skip("FastAPI not installed")

if __name__ == "__main__":
    pytest.main([__file__])
