import time
import schedule
from datetime import datetime
from typing import List, Dict
from scraper import BuyingGroupScraper
from database import DealDatabase
from notifier import DiscordNotifier
from logger import (
    setup_logger, log_monitoring_start, log_check_start, log_check_complete,
    log_new_deal, log_existing_deal, log_quantity_update, log_commitment_update,
    log_auto_commit, log_error, log_discord_notification
)
from config import CHECK_INTERVAL_MINUTES, AUTO_COMMIT_NEW_DEALS

class BuyingGroupMonitor:
    def __init__(self):
        self.scraper = BuyingGroupScraper()
        self.database = DealDatabase()
        self.notifier = DiscordNotifier()
        self.logger = setup_logger()
        self.last_check_time = None
    
    def check_for_new_deals(self):
        """Main function to check for new deals and send notifications."""
        log_check_start(self.logger)
        
        try:
            # Scrape current deals
            current_deals = self.scraper.get_deals()
            
            if not current_deals:
                self.logger.warning("No deals found or failed to scrape deals")
                return
            
            self.logger.info(f"Found {len(current_deals)} deals on the website")
            
            new_deals = []
            updated_deals = []
            
            # Process each deal
            for deal in current_deals:
                existing_deal = self.database.get_deal_by_id(deal['deal_id'])
                
                if not existing_deal:
                    # This is a new deal
                    self.database.add_deal(deal)
                    new_deals.append(deal)
                    log_new_deal(self.logger, deal)
                    
                    # Auto-commit if enabled
                    if AUTO_COMMIT_NEW_DEALS:
                        self.logger.info(f"Attempting auto-commit for new deal: {deal['title']}")
                        if self.scraper.auto_commit_deal(deal):
                            log_auto_commit(self.logger, deal, 1)
                            # Update the deal with committed quantity
                            deal['your_commitment'] = 1
                            self.database.update_your_commitment(deal['deal_id'], 1)
                        else:
                            self.logger.warning(f"Auto-commit failed for: {deal['title']}")
                else:
                    log_existing_deal(self.logger, deal)
                    # Check if quantity has changed (deal availability)
                    if existing_deal['current_quantity'] != deal['current_quantity']:
                        old_quantity = existing_deal['current_quantity']
                        self.database.update_deal_quantity(deal['deal_id'], deal['current_quantity'])
                        updated_deals.append({
                            'deal': deal,
                            'old_quantity': old_quantity,
                            'new_quantity': deal['current_quantity']
                        })
                        log_quantity_update(self.logger, deal, old_quantity, deal['current_quantity'])
                    
                    # Check if your commitment has changed
                    if existing_deal.get('your_commitment', 0) != deal.get('your_commitment', 0):
                        old_commitment = existing_deal.get('your_commitment', 0)
                        new_commitment = deal.get('your_commitment', 0)
                        # Update your commitment in database
                        self.database.update_your_commitment(deal['deal_id'], new_commitment)
                        # Send commitment update notification
                        if not self.database.has_notification_been_sent(deal['deal_id'], 'commitment_update'):
                            success = self.notifier.send_commitment_update_notification(deal, old_commitment, new_commitment)
                            log_discord_notification(self.logger, 'commitment_update', success)
                            if success:
                                self.database.mark_notification_sent(deal['deal_id'], 'commitment_update')
                        log_commitment_update(self.logger, deal, old_commitment, new_commitment)
            
            # Send notifications for new deals
            if new_deals:
                # Check if we've already sent a notification for this batch
                # Use the first deal's ID as a batch identifier
                batch_id = f"new_deals_batch_{new_deals[0]['deal_id']}"
                if not self.database.has_notification_been_sent(batch_id, 'new_deal_batch'):
                    success = self.notifier.send_new_deals_notification(new_deals)
                    log_discord_notification(self.logger, 'new_deals', success)
                    if success:
                        self.database.mark_notification_sent(batch_id, 'new_deal_batch')
                        # Also mark individual deals as notified
                        for deal in new_deals:
                            self.database.mark_notification_sent(deal['deal_id'], 'new_deal')
            
            # Send notifications for quantity updates
            for update in updated_deals:
                if not self.database.has_notification_been_sent(update['deal']['deal_id'], 'quantity_update'):
                    success = self.notifier.send_deal_update_notification(
                        update['deal'], 
                        update['old_quantity'], 
                        update['new_quantity']
                    )
                    log_discord_notification(self.logger, 'quantity_update', success)
                    if success:
                        self.database.mark_notification_sent(update['deal']['deal_id'], 'quantity_update')
            
            self.last_check_time = datetime.now()
            log_check_complete(self.logger, len(new_deals), len(updated_deals))
                
        except Exception as e:
            error_msg = f"Error during deal check: {str(e)}"
            log_error(self.logger, error_msg, "deal_check")
            self.notifier.send_error_notification(error_msg)
    
    def start_monitoring(self):
        """Start the monitoring process."""
        log_monitoring_start(self.logger)
        
        # Send startup notification
        success = self.notifier.send_startup_notification()
        log_discord_notification(self.logger, 'startup', success)
        
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
            self.logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            error_msg = f"Monitor crashed: {str(e)}"
            log_error(self.logger, error_msg, "monitor_crash")
            self.notifier.send_error_notification(error_msg)
    
    def run_single_check(self):
        """Run a single check for testing purposes."""
        self.logger.info("Running single check...")
        self.check_for_new_deals()
    
    def get_statistics(self):
        """Get statistics about monitored deals."""
        deals = self.database.get_all_deals()
        
        if not deals:
            self.logger.info("No deals in database")
            return
        
        self.logger.info(f"📊 Statistics:")
        self.logger.info(f"Total deals monitored: {len(deals)}")
        
        # Group by store
        stores = {}
        total_value = 0
        
        for deal in deals:
            store = deal['store']
            if store not in stores:
                stores[store] = 0
            stores[store] += 1
            total_value += deal['price'] * deal['max_quantity']
        
        self.logger.info(f"Total potential value: ${total_value:,.2f}")
        self.logger.info(f"Deals by store:")
        for store, count in stores.items():
            self.logger.info(f"  {store}: {count} deals")
        
        # Show recent deals
        self.logger.info(f"🆕 Recent deals:")
        recent_deals = deals[:5]  # Show last 5 deals
        for deal in recent_deals:
            self.logger.info(f"  {deal['title'][:60]}... (${deal['price']:.2f})") 