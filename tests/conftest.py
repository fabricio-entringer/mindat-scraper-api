"""
Test configuration for the test suite.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add the project root to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)

@pytest.fixture
def sample_mineral_data():
    """Sample mineral data for testing."""
    return {
        'mineral_code': 'TEST001',
        'name': 'Test Mineral',
        'description': 'A test mineral for unit testing',
        'location': 'Test Location',
        'url': 'https://test.com/mineral/TEST001',
        'search_term': 'test',
        'scraped_at': 1234567890.0
    }
