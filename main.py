#!/usr/bin/env python3
"""
Main entry point for the Mindat Scraper API.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services import ScraperService, DatabaseService
from app.core import setup_logging, get_data_dir
from config import settings

def run_scraper(search_term: str, headless: bool = True):
    """Run the scraper with given search term."""
    try:
        # Setup logging
        setup_logging(settings.LOG_LEVEL)
        logger = logging.getLogger(__name__)
        
        print(f"🔍 Searching for: {search_term}")
        
        # Initialize scraper
        scraper = ScraperService(headless=headless)
        
        # Search for minerals
        minerals = scraper.search_mineral(search_term)
        
        if not minerals:
            print("❌ No minerals found")
            return
        
        print(f"✅ Found {len(minerals)} minerals")
        
        # Initialize database
        db = DatabaseService(settings.DATABASE_PATH)
        
        # Save minerals to database
        saved_count = 0
        for mineral in minerals:
            if db.save_mineral(mineral):
                saved_count += 1
        
        print(f"💾 Saved {saved_count} minerals to database")
        
        # Display results
        print("\n" + "="*60)
        print("SEARCH RESULTS")
        print("="*60)
        
        for i, mineral in enumerate(minerals, 1):
            print(f"\n{i}. {mineral['name']} (Code: {mineral['mineral_code']})")
            print(f"   Description: {mineral['description'][:100]}...")
            print(f"   Location: {mineral['location']}")
            print(f"   URL: {mineral['url']}")
        
        # Close connections
        scraper.close()
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logging.error(f"Scraper error: {str(e)}")

def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Run the FastAPI server."""
    try:
        import uvicorn
        print(f"🚀 Starting API server on {host}:{port}")
        print(f"📖 API docs will be available at: http://{host}:{port}/docs")
        
        uvicorn.run(
            "app.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn")
    except Exception as e:
        print(f"❌ Error starting API: {str(e)}")

def run_tests():
    """Run the test suite."""
    try:
        import pytest
        print("🧪 Running tests...")
        pytest.main(["-v", "tests/"])
        
    except ImportError:
        print("❌ pytest not installed. Install with: pip install pytest")
        
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Mindat Scraper API - Web scraping and API for mineral data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py scrape "quartz"              # Scrape quartz minerals
  python main.py scrape "pyrite" --show-browser  # Scrape with visible browser
  python main.py api                          # Start API server
  python main.py api --port 8080              # Start API on port 8080
  python main.py test                         # Run tests
        """
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape minerals from mindat.org')
    scrape_parser.add_argument('search_term', help='Term to search for')
    scrape_parser.add_argument('--show-browser', action='store_true',
                              help='Show browser window during scraping')
    
    # API command
    api_parser = subparsers.add_parser('api', help='Start the FastAPI server')
    api_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    api_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    api_parser.add_argument('--no-reload', action='store_true',
                           help='Disable auto-reload')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run the test suite')
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'scrape':
        run_scraper(args.search_term, headless=not args.show_browser)
        
    elif args.command == 'api':
        run_api(args.host, args.port, reload=not args.no_reload)
        
    elif args.command == 'test':
        run_tests()
        
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("QUICK START")
        print("="*60)
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Test scraper: python main.py scrape 'quartz'")
        print("3. Start API: python main.py api")
        print("4. Run tests: python main.py test")
        print("5. Visit API docs: http://localhost:8000/docs")
        print("\nProject structure:")
        print("- app/        # Main application code")
        print("- config/     # Configuration files")
        print("- tests/      # Test files")
        print("- scripts/    # Utility scripts")
        print("- infra/      # Infrastructure files")
        print("- docs/       # Documentation")

if __name__ == "__main__":
    main()
