import requests
import logging
from typing import List, Dict, Optional
from config import DISCORD_WEBHOOK_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
import time

class DiscordNotifier:
    def __init__(self, webhook_url: str = DISCORD_WEBHOOK_URL or ""):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger('discord_notifier')
    
    def _make_request_with_retry(self, url: str, json_data: dict) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and proper error handling."""
        from utils import make_request_with_retry
        return make_request_with_retry('POST', url, self.logger, json=json_data)
    
    def _validate_deal_data(self, deal: Dict) -> bool:
        """Validate deal data before sending to Discord."""
        required_fields = ['title', 'store', 'price', 'max_quantity']
        for field in required_fields:
            if field not in deal or deal[field] is None:
                self.logger.warning(f"Deal missing required field: {field}")
                return False
        return True
    
    def _sanitize_deal_data(self, deal: Dict) -> Dict:
        """Sanitize deal data for Discord embed."""
        sanitized = deal.copy()
        
        # Ensure link is valid
        link = deal.get('link', '')
        if not link or not link.startswith(('http://', 'https://')):
            link = "No link available"
        sanitized['link'] = link
        
        # Ensure delivery_date is not None
        sanitized['delivery_date'] = deal.get('delivery_date', 'N/A')
        
        # Truncate title if too long
        if len(sanitized['title']) > 100:
            sanitized['title'] = sanitized['title'][:97] + "..."
        
        return sanitized
    
    def send_new_deals_notification(self, deals: List[Dict]) -> bool:
        """Send notification about new deals."""
        if not self.webhook_url:
            self.logger.warning("No Discord webhook URL configured - notifications disabled")
            return False
        
        if not deals:
            self.logger.info("No deals to notify about")
            return True
        
        try:
            # Validate and sanitize all deals
            valid_deals = []
            for deal in deals:
                if self._validate_deal_data(deal):
                    valid_deals.append(self._sanitize_deal_data(deal))
                else:
                    self.logger.warning(f"Skipping invalid deal: {deal.get('title', 'Unknown')}")
            
            if not valid_deals:
                self.logger.warning("No valid deals to send notification for")
                return False
            
            # Create embed for Discord
            embed = {
                "title": "🆕 New Buying Group Deals Available!",
                "color": 0x00ff00,  # Green color
                "description": f"Found {len(valid_deals)} new deal(s) on the buying group!",
                "fields": [],
                "footer": {
                    "text": "Buying Group Monitor"
                },
                "timestamp": "2024-01-01T00:00:00.000Z"  # Will be replaced with current time
            }
            
            # Add each deal as a field
            for deal in valid_deals:
                field = {
                    "name": f"💰 {deal['title']}",
                    "value": f"**Store:** {deal['store']}\n"
                            f"**Price:** ${deal['price']:.2f}\n"
                            f"**Max Quantity:** {deal['max_quantity']}\n"
                            f"**Delivery:** {deal['delivery_date']}\n"
                            f"**Link:** [Click Here]({deal['link']})",
                    "inline": False
                }
                embed["fields"].append(field)
            
            # Send to Discord
            payload = {
                "embeds": [embed]
            }
            
            response = self._make_request_with_retry(self.webhook_url, payload)
            if response:
                self.logger.info(f"Successfully sent notification for {len(valid_deals)} new deals")
                return True
            else:
                self.logger.error("Failed to send Discord notification after all retries")
                return False
            
        except Exception as e:
            self.logger.error(f"Error sending Discord notification: {e}", exc_info=True)
            return False
    
    def send_deal_update_notification(self, deal: Dict, old_quantity: int, new_quantity: int) -> bool:
        """Send notification about deal quantity updates."""
        if not self.webhook_url:
            self.logger.warning("No Discord webhook URL configured - notifications disabled")
            return False
        
        if not self._validate_deal_data(deal):
            self.logger.warning("Invalid deal data for update notification")
            return False
        
        try:
            sanitized_deal = self._sanitize_deal_data(deal)
            
            embed = {
                "title": "📊 Deal Quantity Updated",
                "color": 0xffa500,  # Orange color
                "description": f"Quantity changed for: **{sanitized_deal['title']}**",
                "fields": [
                    {
                        "name": "Store",
                        "value": sanitized_deal['store'],
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": f"${sanitized_deal['price']:.2f}",
                        "inline": True
                    },
                    {
                        "name": "Quantity Change",
                        "value": f"{old_quantity} → {new_quantity}",
                        "inline": True
                    },
                    {
                        "name": "Max Quantity",
                        "value": str(sanitized_deal['max_quantity']),
                        "inline": True
                    },
                    {
                        "name": "Link",
                        "value": f"[Click Here]({sanitized_deal['link']})",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Buying Group Monitor"
                }
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = self._make_request_with_retry(self.webhook_url, payload)
            if response:
                self.logger.info(f"Successfully sent quantity update notification for {sanitized_deal['title']}")
                return True
            else:
                self.logger.error("Failed to send quantity update notification after all retries")
                return False
            
        except Exception as e:
            self.logger.error(f"Error sending quantity update notification: {e}", exc_info=True)
            return False
    
    def send_error_notification(self, error_message: str) -> bool:
        """Send notification about errors."""
        if not self.webhook_url:
            self.logger.warning("No Discord webhook URL configured - error notifications disabled")
            return False
        
        try:
            # Truncate error message if too long
            if len(error_message) > 1000:
                error_message = error_message[:997] + "..."
            
            embed = {
                "title": "❌ Buying Group Monitor Error",
                "color": 0xff0000,  # Red color
                "description": f"An error occurred while monitoring the buying group:\n```{error_message}```",
                "footer": {
                    "text": "Buying Group Monitor"
                }
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = self._make_request_with_retry(self.webhook_url, payload)
            if response:
                self.logger.info("Successfully sent error notification")
                return True
            else:
                self.logger.error("Failed to send error notification after all retries")
                return False
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}", exc_info=True)
            return False
    
    def send_startup_notification(self) -> bool:
        """Send notification when the monitor starts up."""
        if not self.webhook_url:
            self.logger.warning("No Discord webhook URL configured - startup notifications disabled")
            return False
        
        try:
            embed = {
                "title": "🚀 Buying Group Monitor Started",
                "color": 0x0099ff,  # Blue color
                "description": "The buying group monitor is now running and will check for new deals periodically.",
                "footer": {
                    "text": "Buying Group Monitor"
                }
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = self._make_request_with_retry(self.webhook_url, payload)
            if response:
                self.logger.info("Successfully sent startup notification")
                return True
            else:
                self.logger.error("Failed to send startup notification after all retries")
                return False
            
        except Exception as e:
            self.logger.error(f"Error sending startup notification: {e}", exc_info=True)
            return False
    
    def send_all_deals_summary(self, deals: List[Dict]) -> bool:
        """Send a summary of all active deals, including commitment and description, to Discord."""
        if not self.webhook_url:
            print("No Discord webhook URL configured")
            return False
        if not deals:
            print("No deals to send in summary.")
            return True
        try:
            embed = {
                "title": "📋 All Active Buying Group Deals",
                "color": 0x3498db,  # Blue
                "description": f"Total active deals: {len(deals)}",
                "fields": [],
                "footer": {"text": "Buying Group Monitor"}
            }
            for deal in deals:
                field = {
                    "name": f"{deal['title'][:100]}",
                    "value": (
                        f"**Store:** {deal['store']}\n"
                        f"**Price:** ${deal['price']:.2f}\n"
                        f"**Max Quantity:** {deal['max_quantity']}\n"
                        f"**Committed:** {deal.get('current_quantity', 0)}\n"
                        f"**Delivery:** {deal.get('delivery_date', 'N/A')}\n"
                        f"**Link:** [Product Link]({deal.get('link', '')})"
                    ),
                    "inline": False
                }
                embed["fields"].append(field)
            payload = {"embeds": [embed]}
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            print(f"Successfully sent all deals summary to Discord.")
            return True
        except Exception as e:
            print(f"Error sending all deals summary: {e}")
            return False
    
    def send_warning_notification(self, warning_message: str) -> bool:
        """Send a warning notification to Discord."""
        if not self.webhook_url:
            self.logger.warning("No Discord webhook URL configured - warning notifications disabled")
            return False
        try:
            # Truncate warning message if too long
            if len(warning_message) > 1000:
                warning_message = warning_message[:997] + "..."
            embed = {
                "title": "⚠️ Buying Group Monitor Warning",
                "color": 0xffcc00,  # Yellow color
                "description": f"A warning occurred while monitoring the buying group:\n```{warning_message}```",
                "footer": {
                    "text": "Buying Group Monitor"
                }
            }
            payload = {"embeds": [embed]}
            response = self._make_request_with_retry(self.webhook_url, payload)
            if response:
                self.logger.info("Successfully sent warning notification")
                return True
            else:
                self.logger.error("Failed to send warning notification after all retries")
                return False
        except Exception as e:
            self.logger.error(f"Error sending warning notification: {e}", exc_info=True)
            return False 