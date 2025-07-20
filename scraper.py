import requests
import re
import time
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from config import (
    BUYING_GROUP_LOGIN_URL, 
    BUYING_GROUP_DASHBOARD_URL, 
    USERNAME, 
    PASSWORD, 
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)
import hashlib
import traceback
from notifier import DiscordNotifier

# Import urllib3 for retry strategy
try:
    from urllib3.util import Retry
    from requests.adapters import HTTPAdapter
except ImportError:
    # Fallback for older versions
    Retry = None
    HTTPAdapter = None

class BuyingGroupScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.is_authenticated = False
        
        # Configure retry strategy
        if Retry and HTTPAdapter:
            retry_strategy = HTTPAdapter(
                max_retries=Retry(
                    total=MAX_RETRIES,
                    backoff_factor=RETRY_DELAY,
                    status_forcelist=[429, 500, 502, 503, 504]
                )
            )
            self.session.mount("http://", retry_strategy)
            self.session.mount("https://", retry_strategy)
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and proper error handling using the same session."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                kwargs.setdefault('timeout', REQUEST_TIMEOUT)
                response = getattr(self.session, method.lower())(url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                print(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    print(f"All {MAX_RETRIES + 1} request attempts failed")
                    return None
        return None
    
    def login(self) -> bool:
        """Login to the buying group website."""
        try:
            if os.getenv('DEBUG', 'false').lower() == 'true':
                print(f"Attempting to login with username: {USERNAME}")
                print(f"Using password: {'*' * len(PASSWORD) if PASSWORD else '(empty)'}")
            
            # First, get the login page to extract CSRF token
            print("Getting login page...")
            login_response = self._make_request_with_retry('GET', BUYING_GROUP_LOGIN_URL)
            
            if not login_response:
                print("Failed to get login page")
                return False
            
            if os.getenv('DEBUG', 'false').lower() == 'true':
                print(f"Login page status: {login_response.status_code}")
                print(f"Login page URL: {login_response.url}")
            
            soup = BeautifulSoup(login_response.text, 'html.parser')
            
            # Extract CSRF token
            csrf_token = None
            
            # Try multiple ways to find the CSRF token
            csrf_input = soup.find('input', {'name': '_token'})
            print(f"CSRF input found: {csrf_input is not None}")
            
            if csrf_input and hasattr(csrf_input, 'get') and not isinstance(csrf_input, str):
                csrf_token = csrf_input.get('value')
                print(f"CSRF token value: {csrf_token[:20] if csrf_token else 'None'}...")
                if not csrf_token:
                    print("CSRF input found but no value attribute")
            
            # If not found, try looking for meta tag
            if not csrf_token:
                meta_csrf = soup.find('meta', {'name': 'csrf-token'})
                if meta_csrf and hasattr(meta_csrf, 'get') and not isinstance(meta_csrf, str):
                    csrf_token = meta_csrf.get('content')
                    print(f"Found CSRF token in meta tag: {csrf_token[:20] if csrf_token else 'None'}...")
            
            # If still not found, try other common names
            if not csrf_token:
                for token_name in ['csrf_token', 'csrf', 'token', '_csrf_token']:
                    token_input = soup.find('input', {'name': token_name})
                    if token_input and hasattr(token_input, 'get') and not isinstance(token_input, str):
                        csrf_token = token_input.get('value')
                        print(f"Found CSRF token with name '{token_name}': {csrf_token[:20] if csrf_token else 'None'}...")
                        break
            
            if not csrf_token:
                print("Could not find CSRF token")
                # Let's look for other possible token fields
                all_inputs = [inp for inp in soup.find_all('input') if hasattr(inp, 'get') and not isinstance(inp, str)]
                print(f"Found {len(all_inputs)} input fields:")
                for inp in all_inputs:
                    name = inp.get('name', 'no-name')
                    print(f"  - {name}")
                return False
            
            # Prepare login data
            login_data = {
                '_token': csrf_token,
                'email': USERNAME,
                'password': PASSWORD,
                'remember': 'on'
            }
            
            print(f"Login data keys: {list(login_data.keys())}")
            print(f"CSRF token length: {len(csrf_token) if csrf_token else 0}")
            print(f"Username: {USERNAME}")
            print(f"Password length: {len(PASSWORD) if PASSWORD else 0}")
            
            print("Submitting login form...")
            # Add Referer header to mimic browser behavior
            headers = dict(self.session.headers)
            headers['Referer'] = BUYING_GROUP_LOGIN_URL
            print(f"Headers: {list(headers.keys())}")
            
            # Perform login as application/x-www-form-urlencoded
            login_response = self._make_request_with_retry(
                'POST',
                BUYING_GROUP_LOGIN_URL,
                data=login_data,
                headers=headers,
                allow_redirects=True
            )
            
            if not login_response:
                print("Failed to submit login form")
                return False
            
            print(f"Login response status: {login_response.status_code}")
            print(f"Login response URL: {login_response.url}")
            print(f"Response headers: {dict(login_response.headers)}")
            
            # If we get a 419 error, let's see the response content
            if login_response.status_code == 419:
                print("Got 419 error - checking response content:")
                print(f"Response text (first 500 chars): {login_response.text[:500]}")
                return False
            
            # Check if login was successful
            if login_response.status_code == 200:
                # Check if we're redirected to dashboard or still on login page
                if 'dashboard' in login_response.url.lower() or 'login' not in login_response.url.lower():
                    self.is_authenticated = True
                    print("Successfully logged in to buying group")
                    return True
                else:
                    print("Login failed - still on login page")
                    # Let's check if there are any error messages
                    soup = BeautifulSoup(login_response.text, 'html.parser')
                    error_messages = soup.find_all(class_=re.compile(r'error|alert|danger'))
                    if error_messages:
                        print("Error messages found:")
                        for error in error_messages:
                            print(f"  - {error.get_text(strip=True)}")
                    if os.getenv('DEBUG', 'false').lower() == 'true':
                        print("--- Login Page HTML Start ---")
                        print(login_response.text)
                        print("--- Login Page HTML End ---")
                    return False
            else:
                print(f"Login failed with status code: {login_response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def get_deals(self) -> List[Dict]:
        """Scrape deals from the dashboard page."""
        if not self.is_authenticated:
            if not self.login():
                return []
        
        try:
            # Get the dashboard page
            response = self._make_request_with_retry('GET', BUYING_GROUP_DASHBOARD_URL)
            
            if not response:
                print("Failed to get dashboard page")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all deal cards
            deal_cards = soup.find_all('div', class_='group relative flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white')
            
            deals = []
            for card in deal_cards:
                deal = self._extract_deal_from_card(card)
                if deal:
                    deals.append(deal)
            
            print(f"Found {len(deals)} deals on the dashboard")
            return deals
            
        except Exception as e:
            print(f"Error scraping deals: {e}")
            return []
    
    def _extract_deal_from_card(self, card) -> Optional[Dict]:
        """Extract deal information from a deal card."""
        try:
            # Extract title
            title_elem = card.find('h3', class_='text-sm font-medium text-gray-900')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            
            # Extract store
            store_elem = card.find('p', class_='text-sm italic')
            store = "Unknown Store"
            if store_elem:
                store_text = store_elem.get_text(strip=True)
                if "From:" in store_text:
                    store = store_text.split("From:")[1].strip()
            
            # Extract price
            price_elem = card.find('p', class_='text-base font-medium text-gray-900')
            price = 0.0
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if "Price:" in price_text:
                    price_str = price_text.split("Price:")[1].strip()
                    # Extract numeric value from price string
                    price_match = re.search(r'\$?([\d,]+\.?\d*)', price_str)
                    if price_match:
                        price = float(price_match.group(1).replace(',', ''))
            
            # Extract link
            link_elem = card.find('a', target='_blank')
            link = link_elem.get('href') if link_elem else ""
            
            # Extract max quantity from input field
            input_elem = card.find('input', {'type': 'number'})
            max_quantity = 0
            if input_elem:
                max_attr = input_elem.get('max')
                if max_attr:
                    max_quantity = int(max_attr)
            
            # Extract current quantity (if already committed)
            current_quantity = 0
            committed_text = card.find('span', class_='leading-8')
            if committed_text:
                text = committed_text.get_text(strip=True)
                if "You have committed to purchase" in text:
                    quantity_match = re.search(r'(\d+)', text)
                    if quantity_match:
                        current_quantity = int(quantity_match.group(1))
            
            # Extract delivery date from title
            delivery_date = ""
            delivery_match = re.search(r'Deliver by ([^(]+)', title)
            if delivery_match:
                delivery_date = delivery_match.group(1).strip()
            
            # Generate unique deal ID from title and store
            # Use a more stable ID generation to avoid duplicates
            deal_text = f"{store}_{title}".lower().strip()
            deal_id = hashlib.md5(deal_text.encode()).hexdigest()[:16]
            
            # Validate required fields
            if not title or title == "Unknown Title":
                print("Deal card missing title")
                return None
            
            if not store or store == "Unknown Store":
                print("Deal card missing store information")
                return None
            
            # Sanitize link
            if link and not link.startswith(('http://', 'https://')):
                link = f"https://buyinggroup.ca{link}" if link.startswith('/') else ""
            
            return {
                'deal_id': deal_id,
                'title': title,
                'store': store,
                'price': price,
                'max_quantity': max_quantity,
                'current_quantity': current_quantity,
                'link': link,
                'delivery_date': delivery_date
            }
            
        except Exception as e:
            print(f"Error extracting deal from card: {e}")
            return None
    
    def check_authentication(self) -> bool:
        """Check if the session is still authenticated."""
        try:
            response = self.session.get(BUYING_GROUP_DASHBOARD_URL)
            return response.status_code == 200 and 'login' not in response.url.lower()
        except:
            return False 