"""
Web scraping service for mindat.org using requests and BeautifulSoup.
"""

import logging
import time
import random
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

# Selenium imports (optional, for browser-based scraping)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)

class ScraperService:
    """Web scraper service for mindat.org mineral data using requests."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper with requests session.
        
        Args:
            headless: Whether to run browser in headless mode (for selenium scraping)
        """
        self.session = requests.Session()
        self.base_url = "https://www.mindat.org"
        self.headless = headless
        
        # Set user agent and headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Linux"',
        })
        
        # Set timeout for requests
        self.timeout = 30
        
        # Initialize session by visiting main page to get cookies
        self._initialize_session()
        
    def _initialize_session(self):
        """Initialize session by visiting the main page to establish cookies."""
        try:
            logger.debug("Initializing session with main page visit")
            response = self.session.get(self.base_url, timeout=self.timeout)
            if response.status_code == 200:
                logger.debug("Session initialized successfully")
            else:
                logger.warning(f"Session initialization returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to initialize session: {e}")
        
        # Small delay after initialization
        time.sleep(1)
        
    def _human_delay(self, base_seconds: int = 2) -> None:
        """
        Simulate human-like delay with random variation.
        
        Args:
            base_seconds: Base delay time in seconds
        """
        # Add random variation of ±20% to make it more human-like
        variation = random.uniform(0.8, 1.2)
        delay = base_seconds * variation
        time.sleep(delay)
        logger.debug(f"Waited {delay:.2f} seconds to avoid bot detection")
        
    def _get_page(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Get a page with retry logic and error handling.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retries
            
        Returns:
            Response object if successful, None otherwise
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching URL: {url} (attempt {attempt + 1})")
                
                # Add referer for direct mineral page requests
                headers = {}
                if '/min-' in url:
                    headers['Referer'] = 'https://www.mindat.org/'
                
                response = self.session.get(url, timeout=self.timeout, headers=headers)
                response.raise_for_status()
                
                # Add delay between requests
                self._human_delay(1)
                
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = (2 ** attempt) * random.uniform(1, 2)
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
        
        return None
    
    def search_mineral(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for minerals on mindat.org.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of mineral data dictionaries
        """
        minerals = []
        
        try:
            logger.info(f"Searching for: {search_term}")
            
            # Construct search URL - mindat.org uses a different search format
            search_url = f"{self.base_url}/search.php"
            
            # Search parameters
            params = {
                'search': search_term,
                'submit_search': 'Search'
            }
            
            # Make the search request
            response = self._get_page(search_url, max_retries=3)
            if not response:
                logger.error("Failed to get search page")
                return minerals
            
            # If we get redirected to a single mineral page, handle it
            if '/min-' in response.url and response.url.endswith('.html'):
                mineral_data = self._scrape_mineral_page(response.text, response.url, search_term)
                if mineral_data:
                    minerals.append(mineral_data)
                return minerals
            
            # Parse search results
            soup = BeautifulSoup(response.text, 'html.parser')
            minerals = self._parse_search_results(soup, search_term)
            
            logger.info(f"Found {len(minerals)} minerals")
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            
        return minerals
    
    def _parse_search_results(self, soup: BeautifulSoup, search_term: str) -> List[Dict[str, Any]]:
        """
        Parse search results from the loaded page.
        
        Args:
            soup: BeautifulSoup object of the page
            search_term: Original search term
            
        Returns:
            List of mineral data dictionaries
        """
        minerals = []
        
        try:
            # Look for mineral entries in search results
            # Search for links that look like mineral pages
            mineral_links = soup.find_all('a', href=re.compile(r'/min-\d+\.html'))
            
            for link in mineral_links[:10]:  # Limit to first 10 results
                mineral_data = self._extract_mineral_info_from_link(link, search_term)
                if mineral_data:
                    minerals.append(mineral_data)
            
            # If no results found, try alternative parsing
            if not minerals:
                minerals = self._fallback_parse_results(soup, search_term)
                
        except Exception as e:
            logger.error(f"Error parsing search results: {str(e)}")
        
        return minerals
    
    def _extract_mineral_info_from_link(self, link_element, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Extract mineral information from a link element.
        
        Args:
            link_element: BeautifulSoup element containing mineral link
            search_term: Original search term
            
        Returns:
            Dictionary containing mineral data or None
        """
        try:
            href = link_element.get('href')
            if not href:
                return None
            
            # Extract mineral code from URL
            mineral_code_match = re.search(r'/min-(\d+)\.html', href)
            if not mineral_code_match:
                return None
            
            mineral_code = mineral_code_match.group(1)
            
            # Get mineral name from link text
            name = link_element.get_text(strip=True)
            
            # Try to find additional info in parent/sibling elements
            parent = link_element.parent
            description = ""
            location = ""
            
            if parent:
                # Look for description in nearby elements
                desc_elem = parent.find_next('div', class_=['description', 'summary'])
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                
                # Look for location information
                loc_elem = parent.find_next('div', class_=['location', 'locality'])
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
            
            # Construct full URL
            full_url = urljoin(self.base_url, href)
            
            return {
                'mineral_code': mineral_code,
                'name': name,
                'description': description,
                'location': location,
                'url': full_url,
                'search_term': search_term,
                'scraped_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error extracting mineral info from link: {str(e)}")
            return None
    
    def _extract_mineral_info_from_entry(self, entry_element, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Extract mineral information from a search result entry.
        
        Args:
            entry_element: BeautifulSoup element containing mineral entry
            search_term: Original search term
            
        Returns:
            Dictionary containing mineral data or None
        """
        try:
            # Extract mineral link - try multiple patterns
            link = entry_element.find('a', href=re.compile(r'/min-\d+\.html'))
            if not link:
                return None
            
            href = link.get('href')
            mineral_code_match = re.search(r'/min-(\d+)\.html', href)
            if not mineral_code_match:
                return None
            
            mineral_code = mineral_code_match.group(1)
            name = link.get_text(strip=True)
            
            # For mindat.org, try to extract key mineral properties from the page structure
            description = ""
            location = ""
            
            # Try to find mineral heading and basic info
            mineral_heading = entry_element.find('h1', class_='mineralheading')
            if mineral_heading:
                name = mineral_heading.get_text(strip=True)
            
            # Extract formula if available - look for td with "Formula:" text
            formula_cell = entry_element.find('td', class_='infotabletitle', string='Formula:')
            if formula_cell:
                formula_value = formula_cell.find_next_sibling('td', class_='infotabletext')
                if formula_value:
                    formula = formula_value.get_text(strip=True)
                    description = f"Formula: {formula}"
            
            # Extract color information
            color_cell = entry_element.find('td', class_='infotabletitle', string='Colour:')
            if color_cell:
                color_value = color_cell.find_next_sibling('td', class_='infotabletext')
                if color_value:
                    color = color_value.get_text(strip=True)
                    if description:
                        description += f", Color: {color}"
                    else:
                        description = f"Color: {color}"
            
            # Extract hardness
            hardness_cell = entry_element.find('td', class_='infotabletitle', string='Hardness:')
            if hardness_cell:
                hardness_value = hardness_cell.find_next_sibling('td', class_='infotabletext')
                if hardness_value:
                    hardness = hardness_value.get_text(strip=True)
                    if description:
                        description += f", Hardness: {hardness}"
                    else:
                        description = f"Hardness: {hardness}"
            
            # Extract crystal system
            crystal_cell = entry_element.find('td', class_='infotabletitle', string='Crystal System:')
            if crystal_cell:
                crystal_value = crystal_cell.find_next_sibling('td', class_='infotabletext')
                if crystal_value:
                    crystal = crystal_value.get_text(strip=True)
                    if description:
                        description += f", Crystal System: {crystal}"
                    else:
                        description = f"Crystal System: {crystal}"
            
            # If no description found, try to find any descriptive text
            if not description:
                # Look for introductory text or any descriptive paragraph
                intro_text = entry_element.find('div', class_='padder4')
                if intro_text:
                    description = intro_text.get_text(strip=True)[:200] + "..."
                else:
                    description = f"Mineral found through search: {search_term}"
            
            # Try to extract significant localities
            locality_table = entry_element.find('table', class_='loclisttable')
            if locality_table:
                # Extract a few top localities
                localities = []
                for row in locality_table.find_all('tr')[:3]:  # First 3 localities
                    loc_link = row.find('a', href=re.compile(r'/loc-\d+\.html'))
                    if loc_link:
                        localities.append(loc_link.get_text(strip=True))
                
                if localities:
                    location = ", ".join(localities)
            
            if not location:
                location = "Multiple localities worldwide"
            
            # Construct full URL
            full_url = urljoin(self.base_url, href)
            
            return {
                'mineral_code': mineral_code,
                'name': name,
                'description': description,
                'location': location,
                'url': full_url,
                'search_term': search_term,
                'scraped_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error extracting mineral info from entry: {str(e)}")
            return None
    
    def _fallback_parse_results(self, soup: BeautifulSoup, search_term: str) -> List[Dict[str, Any]]:
        """
        Fallback method to parse results when standard selectors don't work.
        
        Args:
            soup: BeautifulSoup object of the page
            search_term: Original search term
            
        Returns:
            List of mineral data dictionaries
        """
        minerals = []
        
        try:
            # Look for any links that might be mineral pages
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href')
                if href and '/min-' in href and '.html' in href:
                    mineral_code_match = re.search(r'/min-(\d+)\.html', href)
                    if mineral_code_match:
                        mineral_code = mineral_code_match.group(1)
                        name = link.get_text(strip=True)
                        
                        if name and len(name) > 2:  # Basic validation
                            # Construct full URL
                            full_url = urljoin(self.base_url, href)
                            
                            mineral_data = {
                                'mineral_code': mineral_code,
                                'name': name,
                                'description': f"Mineral found through search: {search_term}",
                                'location': "Location not specified",
                                'url': full_url,
                                'search_term': search_term,
                                'scraped_at': time.time()
                            }
                            minerals.append(mineral_data)
                            
                            # Limit results to prevent too many entries
                            if len(minerals) >= 5:
                                break
                                
        except Exception as e:
            logger.error(f"Error in fallback parsing: {str(e)}")
        
        return minerals
    
    def scrape_mineral_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape mineral data from a specific mindat.org URL.
        
        Args:
            url: Direct URL to mineral page (e.g., https://www.mindat.org/min-1720.html)
            
        Returns:
            Dictionary containing mineral data or None if failed
        """
        try:
            # Validate URL format
            if not url.startswith('https://www.mindat.org/min-') or not url.endswith('.html'):
                logger.error(f"Invalid mindat.org mineral URL format: {url}")
                return None
            
            # Extract mineral code from URL
            mineral_code_match = re.search(r'/min-(\d+)\.html', url)
            if not mineral_code_match:
                logger.error(f"Could not extract mineral code from URL: {url}")
                return None
            
            mineral_code = mineral_code_match.group(1)
            
            logger.info(f"Scraping mineral from URL: {url}")
            
            # Try browser-based scraping first if available
            if SELENIUM_AVAILABLE:
                logger.info("Attempting browser-based scraping...")
                mineral_data = self._scrape_with_browser(url, mineral_code)
                if mineral_data:
                    logger.info(f"Successfully scraped mineral {mineral_code} with browser: {mineral_data.get('name', 'Unknown')}")
                    return mineral_data
                else:
                    logger.warning("Browser-based scraping failed, falling back to requests")
            
            # Fallback to requests-based scraping
            response = self._get_page(url)
            if not response:
                logger.error(f"Failed to fetch mineral page: {url}")
                return None
            
            # Parse the page
            mineral_data = self._scrape_mineral_page(response.text, url, f'direct_url_{mineral_code}')
            
            if mineral_data:
                logger.info(f"Successfully scraped mineral {mineral_code}: {mineral_data.get('name', 'Unknown')}")
            
            return mineral_data
            
        except Exception as e:
            logger.error(f"Error scraping mineral from URL {url}: {str(e)}")
            return None
    
    def _scrape_with_browser(self, url: str, mineral_code: str) -> Optional[Dict[str, Any]]:
        """
        Scrape mineral data using Selenium browser automation.
        
        Args:
            url: URL to scrape
            mineral_code: Mineral code for identification
            
        Returns:
            Dictionary containing mineral data or None if failed
        """
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available, cannot use browser scraping")
            return None
        
        driver = None
        try:
            logger.info("Initializing Chrome browser...")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Run in headless mode for now, but can be configured
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Initialize the driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to load and check for Cloudflare challenge
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Check if we're on a Cloudflare challenge page
            if "Checking your browser" in driver.page_source or "cf-browser-verification" in driver.page_source:
                logger.info("Cloudflare challenge detected, waiting for it to resolve...")
                
                # Wait for challenge to resolve (up to 30 seconds)
                for i in range(30):
                    time.sleep(1)
                    if url in driver.current_url and "min-" in driver.current_url:
                        logger.info("Cloudflare challenge resolved successfully")
                        break
                    if i == 29:
                        logger.error("Cloudflare challenge did not resolve in time")
                        return None
            
            # Additional wait to ensure page is fully loaded
            time.sleep(2)
            
            # Get page source and parse with BeautifulSoup
            page_source = driver.page_source
            mineral_data = self._scrape_mineral_page(page_source, url, f'browser_url_{mineral_code}')
            
            return mineral_data
            
        except Exception as e:
            logger.error(f"Error in browser scraping: {str(e)}")
            return None
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _scrape_mineral_page(self, html_content: str, url: str, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Extract mineral data from a mineral page HTML content.
        
        Args:
            html_content: HTML content of the mineral page
            url: URL of the mineral page
            search_term: Original search term or direct URL identifier
            
        Returns:
            Dictionary containing mineral data or None if failed
        """
        try:
            # Extract mineral code from URL
            mineral_code_match = re.search(r'/min-(\d+)\.html', url)
            if not mineral_code_match:
                return None
            
            mineral_code = mineral_code_match.group(1)
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract detailed mineral data
            mineral_data = self._extract_detailed_mineral_data(soup, mineral_code, url, search_term)
            
            return mineral_data
            
        except Exception as e:
            logger.error(f"Error scraping mineral page: {str(e)}")
            return None
    
    def _extract_detailed_mineral_data(self, soup: BeautifulSoup, mineral_code: str, url: str, search_term: str) -> Dict[str, Any]:
        """
        Extract detailed mineral data from the parsed HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            mineral_code: Mineral code extracted from URL
            url: Original URL
            search_term: Original search term
            
        Returns:
            Dictionary containing detailed mineral data
        """
        mineral_data = {
            'mineral_code': mineral_code,
            'name': 'Unknown',
            'url': url,
            'scraped_at': time.time(),
            'properties': {},
            'localities': [],
            'images': [],
            'description': '',
            'location': '',
            'search_term': search_term
        }
        
        try:
            # Extract mineral name from heading
            mineral_heading = soup.find('h1', class_='mineralheading')
            if mineral_heading:
                mineral_data['name'] = mineral_heading.get_text(strip=True)
            
            # Extract introduction/description text
            intro_paragraphs = soup.find_all('p')
            introduction = ""
            for p in intro_paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 50:
                    introduction = text
                    break
            
            if introduction:
                mineral_data['introduction'] = introduction
            
            # Extract properties from both introdata and mindatarow sections
            properties = self._extract_mineral_properties(soup)
            mineral_data['properties'] = properties
            
            # Build description from key properties
            key_props = ['Formula', 'Colour', 'Hardness', 'Crystal System', 'Lustre', 'Transparency']
            description_parts = []
            for prop in key_props:
                if prop in properties:
                    description_parts.append(f"{prop}: {properties[prop]}")
            
            if description_parts:
                mineral_data['description'] = ", ".join(description_parts)
            elif introduction:
                mineral_data['description'] = introduction[:300] + "..." if len(introduction) > 300 else introduction
            else:
                mineral_data['description'] = f"Mineral {mineral_data['name']} (Code: {mineral_code})"
            
            # Extract localities
            localities = self._extract_localities(soup)
            mineral_data['localities'] = localities
            mineral_data['location'] = ", ".join(localities[:5]) if localities else "Multiple localities worldwide"
            
            # Extract images
            images = self._extract_mineral_images(soup)
            mineral_data['images'] = images
            
        except Exception as e:
            logger.error(f"Error extracting detailed mineral data: {str(e)}")
        
        return mineral_data
    
    def _extract_mineral_properties(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract mineral properties from both introdata and mindatarow sections."""
        properties = {}
        
        # First, try to extract from introdata section (basic info)
        intro_section = soup.find('div', id='introdata')
        if intro_section:
            property_divs = intro_section.find_all('div', recursive=False)
            
            for div in property_divs:
                try:
                    span = div.find('span')
                    if span:
                        property_name = span.get_text(strip=True).rstrip(':')
                        
                        # Get the value from the next div
                        value_div = span.find_next_sibling('div')
                        if value_div:
                            # Handle links specially
                            links = value_div.find_all('a')
                            if links:
                                property_value = ', '.join([link.get_text(strip=True) for link in links])
                            else:
                                property_value = value_div.get_text(strip=True)
                            
                            if property_value:
                                properties[property_name] = property_value
                                
                except Exception as e:
                    logger.debug(f"Error extracting intro property: {e}")
        
        # Then, extract from mindatarow sections (detailed info)
        mindatarows = soup.find_all('div', class_='mindatarow')
        if mindatarows:
            for row in mindatarows:
                try:
                    # Find property name
                    th = row.find('div', class_='mindatath')
                    # Find property value
                    td = row.find('div', class_='mindatam2')
                    
                    if th and td:
                        property_name = th.get_text(strip=True).rstrip(':')
                        
                        # Handle links specially
                        links = td.find_all('a')
                        if links:
                            property_value = ', '.join([link.get_text(strip=True) for link in links])
                        else:
                            property_value = td.get_text(strip=True)
                        
                        # Clean up the value
                        property_value = ' '.join(property_value.split())
                        
                        if property_value and property_name:
                            # Skip duplicate properties but keep the most detailed one
                            if property_name not in properties or len(property_value) > len(properties.get(property_name, '')):
                                properties[property_name] = property_value
                                
                except Exception as e:
                    logger.debug(f"Error extracting mindatarow property: {e}")
        
        return properties
    
    def _extract_localities(self, soup: BeautifulSoup) -> List[str]:
        """Extract locality information from the page."""
        localities = []
        
        # Look for locality links
        locality_links = soup.find_all('a', href=lambda x: x and '/loc-' in x)
        
        seen_localities = set()
        for link in locality_links:
            try:
                locality = link.get_text(strip=True)
                if locality and locality not in seen_localities and len(locality) > 3:
                    localities.append(locality)
                    seen_localities.add(locality)
                    
                    # Limit to reasonable number
                    if len(localities) >= 20:
                        break
                        
            except Exception as e:
                logger.debug(f"Error extracting locality: {e}")
        
        return localities
    
    def _extract_mineral_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract mineral images from the page."""
        images = []
        
        # Look for all images
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            try:
                src = img.get('src')
                alt = img.get('alt', '')
                
                if src:
                    # Filter for actual mineral images (not icons, stars, etc.)
                    if any(exclude in src for exclude in ['star.png', 'icon', 'logo', 'flag', 'uk.svg']):
                        continue
                    
                    # Look for images that might be mineral photos
                    if any(include in src.lower() for include in ['jpg', 'jpeg', 'png', 'gif']):
                        # Construct full URL
                        full_src = urljoin(self.base_url, src)
                        
                        image_info = {
                            'src': full_src,
                            'alt': alt.strip() if alt else 'Mineral image'
                        }
                        
                        images.append(image_info)
                        
                        # Limit to reasonable number
                        if len(images) >= 10:
                            break
                            
            except Exception as e:
                logger.debug(f"Error extracting image: {e}")
        
        return images

    def close(self):
        """Close the session."""
        if hasattr(self, 'session'):
            self.session.close()
