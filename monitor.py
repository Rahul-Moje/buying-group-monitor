import time
import schedule
from datetime import datetime
from typing import List, Dict
from scraper import BuyingGroupScraper
from database import DealDatabase
from notifier import DiscordNotifier
from config import CHECK_INTERVAL_MINUTES

class BuyingGroupMonitor:
    def __init__(self):
        self.scraper = BuyingGroupScraper()
        self.database = DealDatabase()
        self.notifier = DiscordNotifier()
        self.last_check_time = None
    
    def check_for_new_deals(self):
        """Main function to check for new deals and send notifications."""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new deals...")
        
        try:
            # Scrape current deals
            current_deals = self.scraper.get_deals()
            
            if not current_deals:
                print("No deals found or failed to scrape deals")
                return
            
            print(f"Found {len(current_deals)} deals on the website")
            
            new_deals = []
            updated_deals = []
            
            # Process each deal
            for deal in current_deals:
                existing_deal = self.database.get_deal_by_id(deal['deal_id'])
                
                if not existing_deal:
                    # This is a new deal
                    self.database.add_deal(deal)
                    new_deals.append(deal)
                    print(f"New deal found: {deal['title']}")
                else:
                    # Check if quantity has changed (deal availability)
                    if existing_deal['current_quantity'] != deal['current_quantity']:
                        old_quantity = existing_deal['current_quantity']
                        self.database.update_deal_quantity(deal['deal_id'], deal['current_quantity'])
                        updated_deals.append({
                            'deal': deal,
                            'old_quantity': old_quantity,
                            'new_quantity': deal['current_quantity']
                        })
                        print(f"Quantity updated for {deal['title']}: {old_quantity} → {deal['current_quantity']}")
                    
                    # Check if your commitment has changed
                    if existing_deal.get('your_commitment', 0) != deal.get('your_commitment', 0):
                        old_commitment = existing_deal.get('your_commitment', 0)
                        new_commitment = deal.get('your_commitment', 0)
                        # Update your commitment in database
                        self.database.update_your_commitment(deal['deal_id'], new_commitment)
                        # Send commitment update notification
                        if not self.database.has_notification_been_sent(deal['deal_id'], 'commitment_update'):
                            self.notifier.send_commitment_update_notification(deal, old_commitment, new_commitment)
                            self.database.mark_notification_sent(deal['deal_id'], 'commitment_update')
                        print(f"Your commitment updated for {deal['title']}: {old_commitment} → {new_commitment}")
            
            # Send notifications for new deals
            if new_deals:
                if not self.database.has_notification_been_sent(new_deals[0]['deal_id'], 'new_deal'):
                    self.notifier.send_new_deals_notification(new_deals)
                    for deal in new_deals:
                        self.database.mark_notification_sent(deal['deal_id'], 'new_deal')
            
            # Send notifications for quantity updates
            for update in updated_deals:
                if not self.database.has_notification_been_sent(update['deal']['deal_id'], 'quantity_update'):
                    self.notifier.send_deal_update_notification(
                        update['deal'], 
                        update['old_quantity'], 
                        update['new_quantity']
                    )
                    self.database.mark_notification_sent(update['deal']['deal_id'], 'quantity_update')
            
            self.last_check_time = datetime.now()
            
            if new_deals or updated_deals:
                print(f"Summary: {len(new_deals)} new deals, {len(updated_deals)} updated deals")
            else:
                print("No new deals or updates found")
                
        except Exception as e:
            error_msg = f"Error during deal check: {str(e)}"
            print(error_msg)
            self.notifier.send_error_notification(error_msg)
    
    def start_monitoring(self):
        """Start the monitoring process."""
        print("🚀 Starting Buying Group Monitor...")
        print(f"Will check for new deals every {CHECK_INTERVAL_MINUTES} minutes")
        
        # Send startup notification
        self.notifier.send_startup_notification()
        
        # Schedule the monitoring job
        schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(self.check_for_new_deals)
        
        # Run initial check
        self.check_for_new_deals()
        
        # Keep the script running
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            self.notifier.send_error_notification(f"Monitor crashed: {str(e)}")
    
    def run_single_check(self):
        """Run a single check for testing purposes."""
        print("Running single check...")
        self.check_for_new_deals()
    
    def get_statistics(self):
        """Get statistics about monitored deals."""
        deals = self.database.get_all_deals()
        
        if not deals:
            print("No deals in database")
            return
        
        print(f"\n📊 Statistics:")
        print(f"Total deals monitored: {len(deals)}")
        
        # Group by store
        stores = {}
        total_value = 0
        
        for deal in deals:
            store = deal['store']
            if store not in stores:
                stores[store] = 0
            stores[store] += 1
            total_value += deal['price'] * deal['max_quantity']
        
        print(f"Total potential value: ${total_value:,.2f}")
        print(f"Deals by store:")
        for store, count in stores.items():
            print(f"  {store}: {count} deals")
        
        # Show recent deals
        print(f"\n🆕 Recent deals:")
        recent_deals = deals[:5]  # Show last 5 deals
        for deal in recent_deals:
            print(f"  {deal['title'][:60]}... (${deal['price']:.2f})") 