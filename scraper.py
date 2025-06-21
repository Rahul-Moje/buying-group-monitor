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
    AUTO_COMMIT_NEW_DEALS,
    AUTO_COMMIT_QUANTITY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)
import hashlib
import logging
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
        self.logger = logging.getLogger(__name__)
        
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
        """Make HTTP request with retry logic and proper error handling."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                kwargs.setdefault('timeout', REQUEST_TIMEOUT)
                response = getattr(self.session, method.lower())(url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error(f"All {MAX_RETRIES + 1} request attempts failed")
                    return None
        return None
    
    def login(self) -> bool:
        """Login to the buying group website."""
        try:
            if os.getenv('DEBUG', 'false').lower() == 'true':
                self.logger.debug(f"Attempting to login with username: {USERNAME}")
                self.logger.debug(f"Using password: {'*' * len(PASSWORD) if PASSWORD else '(empty)'}")
            
            # First, get the login page to extract CSRF token
            self.logger.info("Getting login page...")
            login_response = self._make_request_with_retry('GET', BUYING_GROUP_LOGIN_URL)
            
            if not login_response:
                self.logger.error("Failed to get login page")
                return False
            
            self.logger.debug(f"Login page status: {login_response.status_code}")
            self.logger.debug(f"Login page URL: {login_response.url}")
            
            soup = BeautifulSoup(login_response.text, 'html.parser')
            
            # Extract CSRF token
            csrf_token = None
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input and hasattr(csrf_input, 'get') and not isinstance(csrf_input, str):
                csrf_token = csrf_input.get('value')
                if csrf_token:
                    self.logger.debug(f"Found CSRF token: {csrf_token[:20]}...")
                else:
                    self.logger.warning("CSRF input found but no value attribute")
            else:
                self.logger.warning("Could not find CSRF token input field")
                # Let's look for other possible token fields
                all_inputs = [inp for inp in soup.find_all('input') if hasattr(inp, 'get') and not isinstance(inp, str)]
                self.logger.debug(f"Found {len(all_inputs)} input fields:")
                for inp in all_inputs:
                    name = inp.get('name', 'no-name')
                    self.logger.debug(f"  - {name}")
            
            if not csrf_token:
                self.logger.error("Could not find CSRF token")
                return False
            
            # Prepare login data
            login_data = {
                '_token': csrf_token,
                'email': USERNAME,
                'password': PASSWORD,
                'remember': 'on'
            }
            
            self.logger.info("Submitting login form...")
            # Add Referer header to mimic browser behavior
            headers = dict(self.session.headers)
            headers['Referer'] = BUYING_GROUP_LOGIN_URL
            
            # Perform login as application/x-www-form-urlencoded
            login_response = self._make_request_with_retry(
                'POST',
                BUYING_GROUP_LOGIN_URL,
                data=login_data,
                headers=headers,
                allow_redirects=True
            )
            
            if not login_response:
                self.logger.error("Failed to submit login form")
                return False
            
            self.logger.debug(f"Login response status: {login_response.status_code}")
            self.logger.debug(f"Login response URL: {login_response.url}")
            
            # Check if login was successful
            if login_response.status_code == 200:
                # Check if we're redirected to dashboard or still on login page
                if 'dashboard' in login_response.url.lower() or 'login' not in login_response.url.lower():
                    self.is_authenticated = True
                    self.logger.info("Successfully logged in to buying group")
                    return True
                else:
                    self.logger.warning("Login failed - still on login page")
                    # Let's check if there are any error messages
                    soup = BeautifulSoup(login_response.text, 'html.parser')
                    error_messages = soup.find_all(class_=re.compile(r'error|alert|danger'))
                    if error_messages:
                        self.logger.warning("Error messages found:")
                        for error in error_messages:
                            self.logger.warning(f"  - {error.get_text(strip=True)}")
                    if os.getenv('DEBUG', 'false').lower() == 'true':
                        self.logger.debug("--- Login Page HTML Start ---")
                        self.logger.debug(login_response.text)
                        self.logger.debug("--- Login Page HTML End ---")
                    return False
            else:
                self.logger.error(f"Login failed with status code: {login_response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during login: {e}", exc_info=True)
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
                self.logger.error("Failed to get dashboard page")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all deal cards
            deal_cards = soup.find_all('div', class_='group relative flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white')
            
            deals = []
            for card in deal_cards:
                deal = self._extract_deal_from_card(card)
                if deal:
                    deals.append(deal)
            
            self.logger.info(f"Found {len(deals)} deals on the dashboard")
            return deals
            
        except Exception as e:
            self.logger.error(f"Error scraping deals: {e}", exc_info=True)
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
                self.logger.warning("Deal card missing title")
                return None
            
            if not store or store == "Unknown Store":
                self.logger.warning("Deal card missing store information")
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
            self.logger.error(f"Error extracting deal from card: {e}", exc_info=True)
            return None
    
    def check_authentication(self) -> bool:
        """Check if the session is still authenticated."""
        try:
            response = self.session.get(BUYING_GROUP_DASHBOARD_URL)
            return response.status_code == 200 and 'login' not in response.url.lower()
        except:
            return False
    
    def auto_commit_deal(self, deal: Dict) -> bool:
        """Automatically commit to a deal by submitting the form. Sends Discord error notifications on failure or special cases."""
        try:
            # Find the commit form for this deal
            response = self.session.get(BUYING_GROUP_DASHBOARD_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            deal_cards = soup.find_all('div', class_='group relative flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white')
            
            for card in deal_cards:
                title_elem = card.find('h3', class_='text-sm font-medium text-gray-900')
                title = title_elem.get_text(strip=True) if title_elem else ""
                store_elem = card.find('p', class_='text-sm italic')
                store = ""
                if store_elem:
                    store_text = store_elem.get_text(strip=True)
                    if "From:" in store_text:
                        store = store_text.split("From:")[1].strip()
                
                if title == deal['title'] and store == deal['store']:
                    # Look for the new form structure with wire:model.lazy attributes
                    amount_input = card.find('input', attrs={'wire:model.lazy': re.compile(r'commitments\.\d+\.amount')})
                    
                    if amount_input:
                        # Extract the deal ID from the wire:model.lazy attribute
                        wire_model = amount_input.get('wire:model.lazy', '')
                        deal_id_match = re.search(r'commitments\.(\d+)\.amount', wire_model)
                        
                        if deal_id_match:
                            deal_id = deal_id_match.group(1)
                            self.logger.info(f"Found deal ID {deal_id} for {deal['title']}")
                            
                            # Get CSRF token from page
                            csrf_token = None
                            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
                            if csrf_meta:
                                csrf_token = csrf_meta.get('content')
                            
                            if not csrf_token:
                                # Try alternative CSRF token locations
                                csrf_input = soup.find('input', {'name': '_token'})
                                if csrf_input and hasattr(csrf_input, 'get') and not isinstance(csrf_input, str):
                                    csrf_token = csrf_input.get('value')
                            
                            if csrf_token:
                                # Prepare the commit data for Livewire
                                commit_data = {
                                    '_token': csrf_token,
                                    'commitments': {
                                        deal_id: {
                                            'amount': AUTO_COMMIT_QUANTITY
                                        }
                                    }
                                }
                                
                                # Try to find the Livewire update endpoint
                                # Look for any Livewire-related scripts or data attributes
                                livewire_id = None
                                livewire_elem = card.find(attrs={'wire:id': True})
                                if livewire_elem:
                                    livewire_id = livewire_elem.get('wire:id')
                                
                                # If we can't find a specific Livewire ID, try the general update endpoint
                                if livewire_id:
                                    update_url = f"https://buyinggroup.ca/livewire/message/{livewire_id}"
                                else:
                                    # Try to find the form action or use a general endpoint
                                    form = card.find('form')
                                    if form and form.get('action'):
                                        update_url = form.get('action')
                                        if not update_url.startswith('http'):
                                            update_url = f"https://buyinggroup.ca{update_url}"
                                    else:
                                        # Use a general Livewire update endpoint
                                        update_url = "https://buyinggroup.ca/livewire/update"
                                
                                self.logger.info(f"Attempting to commit deal {deal_id} with quantity {AUTO_COMMIT_QUANTITY}")
                                
                                # First attempt with default quantity
                                headers = {
                                    'Content-Type': 'application/json',
                                    'X-CSRF-TOKEN': csrf_token,
                                    'X-Requested-With': 'XMLHttpRequest'
                                }
                                
                                # Try JSON format first (Livewire standard)
                                try:
                                    json_data = {
                                        'fingerprint': {
                                            'id': livewire_id or 'commitment-form',
                                            'name': 'commitment-form',
                                            'locale': 'en',
                                            'path': '/dashboard',
                                            'method': 'GET'
                                        },
                                        'serverMemo': {
                                            'children': [],
                                            'errors': {},
                                            'htmlHash': '',
                                            'data': {
                                                'commitments': {
                                                    deal_id: {
                                                        'amount': AUTO_COMMIT_QUANTITY
                                                    }
                                                }
                                            },
                                            'dataMeta': [],
                                            'checksum': ''
                                        },
                                        'updates': [
                                            {
                                                'type': 'callMethod',
                                                'payload': {
                                                    'id': f'commitment-{deal_id}',
                                                    'method': 'updateCommitment',
                                                    'params': [deal_id, AUTO_COMMIT_QUANTITY]
                                                }
                                            }
                                        ]
                                    }
                                    
                                    commit_response = self.session.post(
                                        update_url,
                                        json=json_data,
                                        headers=headers
                                    )
                                    
                                    if commit_response.status_code == 200:
                                        # Check for "Must buy X or more" error in response
                                        response_text = commit_response.text.lower()
                                        if "must buy" in response_text and "or more" in response_text:
                                            # Extract minimum quantity and retry
                                            patterns = [
                                                r'must buy (\d+) or more',
                                                r'minimum (\d+)',
                                                r'at least (\d+)',
                                                r'buy (\d+) or more'
                                            ]
                                            
                                            min_qty = None
                                            for pattern in patterns:
                                                match = re.search(pattern, response_text)
                                                if match:
                                                    min_qty = int(match.group(1))
                                                    break
                                            
                                            if min_qty and min_qty > AUTO_COMMIT_QUANTITY:
                                                error_msg = f"Auto-commit failed for {deal['title']}: Must buy at least {min_qty}. Retrying with {min_qty}.\nStack trace:\n{traceback.format_exc()}"
                                                DiscordNotifier().send_error_notification(error_msg)
                                                self.logger.warning(f"Auto-commit failed for {deal['title']}: Must buy at least {min_qty}. Retrying with {min_qty}.")
                                                
                                                # Retry with the correct minimum quantity
                                                json_data['serverMemo']['data']['commitments'][deal_id]['amount'] = min_qty
                                                json_data['updates'][0]['payload']['params'][1] = min_qty
                                                
                                                commit_response2 = self.session.post(
                                                    update_url,
                                                    json=json_data,
                                                    headers=headers
                                                )
                                                
                                                if commit_response2.status_code == 200:
                                                    retry_text = commit_response2.text.lower()
                                                    if "must buy" not in retry_text and "error" not in retry_text:
                                                        success_msg = f"Auto-commit succeeded for {deal['title']} with quantity {min_qty}"
                                                        DiscordNotifier().send_warning_notification(success_msg)
                                                        self.logger.info(success_msg)
                                                        return True
                                                    else:
                                                        error_msg = f"Auto-commit retry failed for {deal['title']} with quantity {min_qty}. Response: {retry_text[:200]}\nStack trace:\n{traceback.format_exc()}"
                                                        DiscordNotifier().send_error_notification(error_msg)
                                                        self.logger.warning(f"Auto-commit retry failed for {deal['title']} with quantity {min_qty}. Response: {retry_text[:200]}")
                                                        return False
                                                else:
                                                    error_msg = f"Auto-commit retry failed with status {commit_response2.status_code} for {deal['title']}\nStack trace:\n{traceback.format_exc()}"
                                                    DiscordNotifier().send_error_notification(error_msg)
                                                    self.logger.warning(f"Auto-commit retry failed with status {commit_response2.status_code} for {deal['title']}")
                                                    return False
                                            else:
                                                error_msg = f"Auto-commit failed for {deal['title']}: Could not determine minimum quantity from response: {response_text[:200]}\nStack trace:\n{traceback.format_exc()}"
                                                DiscordNotifier().send_error_notification(error_msg)
                                                self.logger.warning(f"Auto-commit failed for {deal['title']}: Could not determine minimum quantity from response: {response_text[:200]}")
                                                return False
                                        else:
                                            # No "Must buy" error, commit was successful
                                            success_msg = f"Auto-commit succeeded for {deal['title']} with quantity {AUTO_COMMIT_QUANTITY}"
                                            DiscordNotifier().send_warning_notification(success_msg)
                                            self.logger.info(success_msg)
                                            return True
                                    else:
                                        error_msg = f"Commit failed with status {commit_response.status_code} for {deal['title']}\nStack trace:\n{traceback.format_exc()}"
                                        DiscordNotifier().send_error_notification(error_msg)
                                        self.logger.warning(f"Commit failed with status {commit_response.status_code} for {deal['title']}")
                                        return False
                                        
                                except Exception as json_error:
                                    self.logger.warning(f"JSON commit failed, trying form data: {json_error}")
                                    
                                    # Fallback to form data approach
                                    form_data = {
                                        '_token': csrf_token,
                                        f'commitments.{deal_id}.amount': AUTO_COMMIT_QUANTITY
                                    }
                                    
                                    commit_response = self.session.post(
                                        update_url,
                                        data=form_data,
                                        headers={'X-Requested-With': 'XMLHttpRequest'}
                                    )
                                    
                                    if commit_response.status_code == 200:
                                        response_text = commit_response.text.lower()
                                        if "must buy" in response_text and "or more" in response_text:
                                            # Handle minimum quantity retry for form data
                                            patterns = [
                                                r'must buy (\d+) or more',
                                                r'minimum (\d+)',
                                                r'at least (\d+)',
                                                r'buy (\d+) or more'
                                            ]
                                            
                                            min_qty = None
                                            for pattern in patterns:
                                                match = re.search(pattern, response_text)
                                                if match:
                                                    min_qty = int(match.group(1))
                                                    break
                                            
                                            if min_qty and min_qty > AUTO_COMMIT_QUANTITY:
                                                error_msg = f"Auto-commit failed for {deal['title']}: Must buy at least {min_qty}. Retrying with {min_qty}.\nStack trace:\n{traceback.format_exc()}"
                                                DiscordNotifier().send_error_notification(error_msg)
                                                self.logger.warning(f"Auto-commit failed for {deal['title']}: Must buy at least {min_qty}. Retrying with {min_qty}.")
                                                
                                                form_data[f'commitments.{deal_id}.amount'] = min_qty
                                                
                                                commit_response2 = self.session.post(
                                                    update_url,
                                                    data=form_data,
                                                    headers={'X-Requested-With': 'XMLHttpRequest'}
                                                )
                                                
                                                if commit_response2.status_code == 200:
                                                    retry_text = commit_response2.text.lower()
                                                    if "must buy" not in retry_text and "error" not in retry_text:
                                                        success_msg = f"Auto-commit succeeded for {deal['title']} with quantity {min_qty}"
                                                        DiscordNotifier().send_warning_notification(success_msg)
                                                        self.logger.info(success_msg)
                                                        return True
                                                    else:
                                                        error_msg = f"Auto-commit retry failed for {deal['title']} with quantity {min_qty}. Response: {retry_text[:200]}\nStack trace:\n{traceback.format_exc()}"
                                                        DiscordNotifier().send_error_notification(error_msg)
                                                        self.logger.warning(f"Auto-commit retry failed for {deal['title']} with quantity {min_qty}. Response: {retry_text[:200]}")
                                                        return False
                                                else:
                                                    error_msg = f"Auto-commit retry failed with status {commit_response2.status_code} for {deal['title']}\nStack trace:\n{traceback.format_exc()}"
                                                    DiscordNotifier().send_error_notification(error_msg)
                                                    self.logger.warning(f"Auto-commit retry failed with status {commit_response2.status_code} for {deal['title']}")
                                                    return False
                                            else:
                                                error_msg = f"Auto-commit failed for {deal['title']}: Could not determine minimum quantity from response: {response_text[:200]}\nStack trace:\n{traceback.format_exc()}"
                                                DiscordNotifier().send_error_notification(error_msg)
                                                self.logger.warning(f"Auto-commit failed for {deal['title']}: Could not determine minimum quantity from response: {response_text[:200]}")
                                                return False
                                        else:
                                            # No "Must buy" error, commit was successful
                                            success_msg = f"Auto-commit succeeded for {deal['title']} with quantity {AUTO_COMMIT_QUANTITY}"
                                            DiscordNotifier().send_warning_notification(success_msg)
                                            self.logger.info(success_msg)
                                            return True
                                    else:
                                        error_msg = f"Form commit failed with status {commit_response.status_code} for {deal['title']}\nStack trace:\n{traceback.format_exc()}"
                                        DiscordNotifier().send_error_notification(error_msg)
                                        self.logger.warning(f"Form commit failed with status {commit_response.status_code} for {deal['title']}")
                                        return False
                            else:
                                error_msg = f"Could not find CSRF token for commit for {deal['title']}\nStack trace:\n{traceback.format_exc()}"
                                DiscordNotifier().send_error_notification(error_msg)
                                self.logger.warning(f"Could not find CSRF token for commit for {deal['title']}")
                                return False
                        else:
                            error_msg = f"Could not extract deal ID from wire:model.lazy for {deal['title']}\nStack trace:\n{traceback.format_exc()}"
                            DiscordNotifier().send_error_notification(error_msg)
                            self.logger.warning(f"Could not extract deal ID from wire:model.lazy for {deal['title']}")
                            return False
                    else:
                        error_msg = f"Could not find amount input with wire:model.lazy for deal {deal['title']}\nStack trace:\n{traceback.format_exc()}"
                        DiscordNotifier().send_error_notification(error_msg)
                        self.logger.warning(f"Could not find amount input with wire:model.lazy for deal {deal['title']}")
                        return False
            
            error_msg = f"Could not find deal card for: {deal['title']}\nStack trace:\n{traceback.format_exc()}"
            DiscordNotifier().send_error_notification(error_msg)
            self.logger.warning(f"Could not find deal card for: {deal['title']}")
            return False
            
        except Exception as e:
            error_msg = f"Error during auto-commit for {deal.get('title', 'Unknown')}: {e}\nStack trace:\n{traceback.format_exc()}"
            DiscordNotifier().send_error_notification(error_msg)
            self.logger.error(f"Error during auto-commit for {deal.get('title', 'Unknown')}: {e}")
            return False 