import requests
from typing import List, Dict
from config import DISCORD_WEBHOOK_URL

class DiscordNotifier:
    def __init__(self, webhook_url: str = DISCORD_WEBHOOK_URL):
        self.webhook_url = webhook_url
    
    def send_new_deals_notification(self, deals: List[Dict]) -> bool:
        """Send notification about new deals."""
        if not self.webhook_url:
            print("No Discord webhook URL configured")
            return False
        
        if not deals:
            return True
        
        try:
            # Create embed for Discord
            embed = {
                "title": "🆕 New Buying Group Deals Available!",
                "color": 0x00ff00,  # Green color
                "description": f"Found {len(deals)} new deal(s) on the buying group!",
                "fields": [],
                "footer": {
                    "text": "Buying Group Monitor"
                },
                "timestamp": "2024-01-01T00:00:00.000Z"  # Will be replaced with current time
            }
            
            # Add each deal as a field
            for deal in deals:
                field = {
                    "name": f"💰 {deal['title'][:100]}...",
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
            
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            print(f"Successfully sent notification for {len(deals)} new deals")
            return True
            
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
            return False
    
    def send_deal_update_notification(self, deal: Dict, old_quantity: int, new_quantity: int) -> bool:
        """Send notification about deal quantity updates."""
        if not self.webhook_url:
            print("No Discord webhook URL configured")
            return False
        
        try:
            embed = {
                "title": "📊 Deal Quantity Updated",
                "color": 0xffa500,  # Orange color
                "description": f"Quantity changed for: **{deal['title']}**",
                "fields": [
                    {
                        "name": "Store",
                        "value": deal['store'],
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": f"${deal['price']:.2f}",
                        "inline": True
                    },
                    {
                        "name": "Quantity Change",
                        "value": f"{old_quantity} → {new_quantity}",
                        "inline": True
                    },
                    {
                        "name": "Max Quantity",
                        "value": str(deal['max_quantity']),
                        "inline": True
                    },
                    {
                        "name": "Link",
                        "value": f"[Click Here]({deal['link']})",
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
            
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            print(f"Successfully sent quantity update notification for {deal['title']}")
            return True
            
        except Exception as e:
            print(f"Error sending quantity update notification: {e}")
            return False
    
    def send_error_notification(self, error_message: str) -> bool:
        """Send notification about errors."""
        if not self.webhook_url:
            print("No Discord webhook URL configured")
            return False
        
        try:
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
            
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            print("Successfully sent error notification")
            return True
            
        except Exception as e:
            print(f"Error sending error notification: {e}")
            return False
    
    def send_startup_notification(self) -> bool:
        """Send notification when the monitor starts up."""
        if not self.webhook_url:
            print("No Discord webhook URL configured")
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
            
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            print("Successfully sent startup notification")
            return True
            
        except Exception as e:
            print(f"Error sending startup notification: {e}")
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
    
    def send_commitment_update_notification(self, deal: Dict, old_commitment: int, new_commitment: int) -> bool:
        """Send notification about commitment quantity updates."""
        if not self.webhook_url:
            print("No Discord webhook URL configured")
            return False
        
        try:
            embed = {
                "title": "📝 Commitment Updated",
                "color": 0x9b59b6,  # Purple color
                "description": f"Your commitment changed for: **{deal['title']}**",
                "fields": [
                    {
                        "name": "Store",
                        "value": deal['store'],
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": f"${deal['price']:.2f}",
                        "inline": True
                    },
                    {
                        "name": "Commitment Change",
                        "value": f"{old_commitment} → {new_commitment}",
                        "inline": True
                    },
                    {
                        "name": "Max Available",
                        "value": str(deal['max_quantity']),
                        "inline": True
                    },
                    {
                        "name": "Delivery",
                        "value": deal.get('delivery_date', 'N/A'),
                        "inline": True
                    },
                    {
                        "name": "Link",
                        "value": f"[Product Link]({deal.get('link', '')})",
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
            
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            print(f"Successfully sent commitment update notification for {deal['title']}")
            return True
            
        except Exception as e:
            print(f"Error sending commitment update notification: {e}")
            return False 