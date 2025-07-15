# Mindat Scraper API

MindatScraperAPI is an open-source project that performs automated web scraping on Mindat.org to extract information about minerals and rocks. The data is processed and made available through a clean RESTful API, allowing researchers, educators, and developers to easily integrate Mindat's mineralogical data into their own applications.

## Features

- 🔍 **Web Scraping**: Automated scraping of mindat.org using requests and BeautifulSoup
- 🌐 **URL Scraping**: Direct scraping from specific mindat.org URLs
- 💾 **Data Storage**: Local JSON database using TinyDB
- 🚀 **REST API**: FastAPI-based endpoints for data access
- 📱 **Easy Integration**: Simple HTTP endpoints for external applications
- 🧪 **Testing**: Comprehensive test suite included
- 📖 **Documentation**: Well-documented code and API endpoints

## Project Structure

```
mindat-scraper-api/
├── app/                     # Main application code
│   ├── __init__.py
│   ├── api/                 # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app setup
│   │   └── minerals.py      # Mineral API routes
│   ├── core/                # Core utilities
│   │   ├── __init__.py
│   │   └── utils.py         # Utility functions
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   └── mineral.py       # Mineral data models
│   └── services/            # Business logic
│       ├── __init__.py
│       ├── database.py      # Database service
│       └── scraper.py       # Web scraping service
├── config/                  # Configuration files
│   ├── __init__.py
│   └── settings.py          # Application settings
├── tests/                   # Test files
│   ├── __init__.py
│   ├── conftest.py          # Test configuration
│   └── test_services.py     # Service tests
├── scripts/                 # Utility scripts
│   ├── cli.py               # Command-line interface
│   ├── example.py           # Usage examples
│   └── test_api.py          # API testing script
├── infra/                   # Infrastructure files
│   ├── Dockerfile           # Docker container config
│   ├── docker-compose.yml   # Docker Compose config
│   └── Makefile            # Build automation
├── docs/                    # Documentation
│   └── PROJECT_SUMMARY.md   # Project summary
├── data/                    # Data files (created at runtime)
│   └── minerals.json        # Database file
├── logs/                    # Log files (created at runtime)
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Chrome or Chromium browser
- Git (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/fabricio-entringer/mindat-scraper-api.git
cd mindat-scraper-api
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Ready to Use

The scraper now uses requests and BeautifulSoup, so no additional setup is required! You can start using the API immediately.

## Usage

### Method 1: Command Line Interface

Test the scraper manually with a search term:

```bash
python cli.py "quartz"
```

Options:
- `--show-browser`: Show the browser window during scraping
- `--headless`: Run in headless mode (default)

Example:
```bash
python cli.py "pyrite" --show-browser
```

### Method 2: REST API

#### Start the FastAPI Server

```bash
python -m uvicorn app.api.main:app --reload
```

The API will be available at `http://localhost:8000`

#### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

#### API Endpoints

##### 1. Search for Minerals

```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"search_term": "quartz", "save_to_db": true}'
```

##### 2. Get Mineral by Code

```bash
curl "http://localhost:8000/mineral/123"
```

##### 3. Get All Minerals

```bash
curl "http://localhost:8000/minerals"
```

##### 4. Search Database

```bash
curl "http://localhost:8000/search/quartz"
```

##### 5. Scrape Mineral from URL

```bash
curl -X POST "http://localhost:8000/scrape-url" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.mindat.org/min-1720.html", "save_to_db": true}'
```

##### 6. Health Check

```bash
curl "http://localhost:8000/health"
```

### Method 3: Direct URL Scraping

#### Command Line Script

```bash
python scripts/scrape_url.py "https://www.mindat.org/min-1720.html"
```

#### API Testing Script

```bash
python scripts/test_url_api.py "https://www.mindat.org/min-1720.html"
```

### Method 4: Python Integration

```python
from app.services import ScraperService, DatabaseService

# Initialize scraper
scraper = ScraperService(headless=True)

# Search for minerals
minerals = scraper.search_mineral("quartz")

# Scrape from specific URL
mineral_data = scraper.scrape_mineral_from_url("https://www.mindat.org/min-1720.html")

# Save to database
db = DatabaseService()
for mineral in minerals:
    db.save_mineral(mineral)

# Save single mineral
if mineral_data:
    db.save_mineral(mineral_data)

# Retrieve from database
saved_mineral = db.get_mineral("123")
```

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

For testing without pytest:

```bash
python tests/test_services.py
```

## Configuration

The application can be configured using environment variables:

```bash
export DATABASE_PATH="custom_minerals.json"
export SCRAPER_HEADLESS="false"
export API_HOST="0.0.0.0"
export API_PORT="8000"
export LOG_LEVEL="DEBUG"
```

## Data Structure

Each mineral record contains:

```json
{
  "mineral_code": "1720",
  "name": "Gold",
  "description": "Formula: Au, Hardness: 2.5-3, Crystal System: Isometric...",
  "location": "California, Alaska, Nevada, Australia, South Africa",
  "url": "https://www.mindat.org/min-1720.html",
  "search_term": "direct_url_1720",
  "scraped_at": 1234567890.0,
  "properties": {
    "Formula": "Au",
    "Hardness": "2.5-3",
    "Crystal System": "Isometric",
    "Colour": "Golden yellow",
    "Lustre": "Metallic",
    "Transparency": "Opaque"
  },
  "localities": [
    "California",
    "Alaska",
    "Nevada",
    "Australia",
    "South Africa"
  ],
  "images": [
    {
      "src": "https://www.mindat.org/images/gold1.jpg",
      "alt": "Gold specimen"
    }
  ],
  "introduction": "Gold is a chemical element with the symbol Au..."
}
```

## Troubleshooting

### Common Issues

1. **Request Issues**
   - Verify internet connection
   - Check if mindat.org is accessible
   - Consider using a VPN if blocked

2. **Connection Errors**
   - Verify internet connection
   - Check if mindat.org is accessible
   - Consider using a VPN if blocked

3. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Activate virtual environment: `source venv/bin/activate`

4. **Database Issues**
   - Check file permissions for `minerals.json`
   - Ensure sufficient disk space

### Debug Mode

Run the scraper with visible browser for debugging:

```bash
python cli.py "test_term" --show-browser
```

Enable debug logging:

```bash
export LOG_LEVEL="DEBUG"
python cli.py "test_term"
```

## Development

### Adding New Features

1. **New Scraping Logic**: Modify `scraper.py`
2. **Database Operations**: Update `database.py`
3. **API Endpoints**: Add to `api.py`
4. **Tests**: Add to `test_scraper.py`

### Running in Development Mode

```bash
# API with auto-reload
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# With debug logging
export LOG_LEVEL="DEBUG"
python -m uvicorn app.api.main:app --reload
```

## Examples

See `example.py` for complete usage examples:

```bash
python example.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Please respect mindat.org's robots.txt and terms of service. Use responsibly and consider the server load.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation at `/docs`

## Changelog

### Version 1.0.0
- Initial release
- Web scraping functionality
- TinyDB integration
- FastAPI REST API
- Command-line interface
- Comprehensive test suitemindat-scraper-api
MindatScraperAPI is an open-source project that performs automated web scraping on Mindat.org to extract information about minerals and rocks. The data is processed and made available through a clean RESTful API, allowing researchers, educators, and developers to easily integrate Mindat’s mineralogical data into their own applications.
