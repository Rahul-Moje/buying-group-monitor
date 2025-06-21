import time
import schedule
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from scraper import BuyingGroupScraper
from database import DealDatabase
from notifier import DiscordNotifier
from logger import setup_logger, log_monitoring_start, log_check_start, log_check_complete, log_error
from config import (
    CHECK_INTERVAL_MINUTES, 
    AUTO_COMMIT_NEW_DEALS, 
    AUTO_COMMIT_QUANTITY,
    LOG_LEVEL,
    LOG_FILE
)
import os
import signal
import sys

class BuyingGroupMonitor:
    def __init__(self):
        self.logger = setup_logger()
        self.scraper = BuyingGroupScraper()
        self.db = DealDatabase()
        self.notifier = DiscordNotifier()
        self.running = False
        self.last_check_time = None
        self.check_count = 0
        self.error_count = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def _validate_environment(self) -> bool:
        """Validate that all required environment variables are set."""
        required_vars = [
            'BUYING_GROUP_USERNAME',
            'BUYING_GROUP_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Validate optional but important variables
        if not os.getenv('DISCORD_WEBHOOK_URL'):
            self.logger.warning("No Discord webhook URL configured - notifications will be disabled")
        
        return True
    
    def _check_connectivity(self) -> bool:
        """Check basic connectivity to the buying group website."""
        try:
            import requests
            response = requests.get('https://app.buyinggroup.ca', timeout=10)
            if response.status_code == 200:
                self.logger.debug("Connectivity check passed")
                return True
            else:
                self.logger.warning(f"Connectivity check failed with status {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Connectivity check failed: {e}")
            return False
    
    def _get_health_status(self) -> Dict:
        """Get current health status of the monitor."""
        return {
            'status': 'running' if self.running else 'stopped',
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'check_count': self.check_count,
            'error_count': self.error_count,
            'uptime': str(datetime.now() - self.start_time) if hasattr(self, 'start_time') else None,
            'database_stats': self.db.get_database_stats()
        }
    
    def start(self):
        """Start the monitoring service."""
        if self.running:
            self.logger.warning("Monitor is already running")
            return
        
        # Validate environment
        if not self._validate_environment():
            self.logger.error("Environment validation failed, cannot start monitor")
            return
        
        # Check connectivity
        if not self._check_connectivity():
            self.logger.warning("Connectivity check failed, but continuing...")
        
        self.running = True
        self.start_time = datetime.now()
        self.logger.info("Starting Buying Group Monitor...")
        
        # Log startup information
        log_monitoring_start(self.logger)
        
        # Send startup notification
        try:
            self.notifier.send_startup_notification()
        except Exception as e:
            self.logger.error(f"Failed to send startup notification: {e}")
        
        # Schedule the monitoring job
        schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(self.check_for_new_deals)
        
        # Run initial check
        self.logger.info("Running initial check...")
        self.check_for_new_deals()
        
        # Start the scheduler
        self.logger.info(f"Monitor started successfully. Checking every {CHECK_INTERVAL_MINUTES} minutes.")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                self.error_count += 1
                time.sleep(60)  # Wait a minute before continuing
    
    def stop(self):
        """Stop the monitoring service."""
        if not self.running:
            return
        
        self.logger.info("Stopping Buying Group Monitor...")
        self.running = False
        schedule.clear()
        
        # Send shutdown notification if possible
        try:
            if hasattr(self, 'notifier'):
                self.notifier.send_error_notification("Monitor stopped by user")
        except Exception as e:
            self.logger.error(f"Failed to send shutdown notification: {e}")
        
        self.logger.info("Monitor stopped successfully")
    
    def check_for_new_deals(self):
        """Check for new deals and send notifications."""
        if not self.running:
            return
        
        self.check_count += 1
        current_time = datetime.now()
        
        try:
            log_check_start(self.logger)
            
            # Get current deals from website
            current_deals = self.scraper.get_deals()
            if not current_deals:
                self.logger.warning("No deals found on website")
                return
            
            self.logger.info(f"Found {len(current_deals)} deals on website")
            
            # Get existing deals from database
            existing_deals = self.db.get_all_deals()
            existing_deal_ids = {deal['deal_id'] for deal in existing_deals}
            
            # Find new deals
            new_deals = []
            updated_deals = []
            
            for deal in current_deals:
                if deal['deal_id'] not in existing_deal_ids:
                    # This is a new deal
                    new_deals.append(deal)
                    
                    # Auto-commit if enabled
                    if AUTO_COMMIT_NEW_DEALS:
                        self.logger.info(f"Attempting auto-commit for new deal: {deal['title']}")
                        if self.scraper.auto_commit_deal(deal):
                            deal['your_commitment'] = AUTO_COMMIT_QUANTITY
                            self.logger.info(f"Auto-commit successful for: {deal['title']}")
                        else:
                            self.logger.warning(f"Auto-commit failed for: {deal['title']}")
                else:
                    # Check if quantity has changed
                    existing_deal = next((d for d in existing_deals if d['deal_id'] == deal['deal_id']), None)
                    if existing_deal and existing_deal['current_quantity'] != deal['current_quantity']:
                        updated_deals.append({
                            'deal': deal,
                            'old_quantity': existing_deal['current_quantity'],
                            'new_quantity': deal['current_quantity']
                        })
            
            # Save all deals to database
            for deal in current_deals:
                self.db.add_deal(deal)
            
            # Send notifications for new deals
            if new_deals:
                self.logger.info(f"Found {len(new_deals)} new deals")
                
                # Create batch ID for notification tracking
                batch_id = f"new_deals_{current_time.strftime('%Y%m%d_%H%M%S')}"
                
                # Check if we've already sent a notification for this batch
                if not self.db.has_notification_been_sent(batch_id):
                    if self.notifier.send_new_deals_notification(new_deals):
                        self.db.mark_notification_sent(batch_id)
                        self.logger.info(f"Sent notification for {len(new_deals)} new deals")
                    else:
                        self.logger.error("Failed to send new deals notification")
                else:
                    self.logger.info("Notification already sent for this batch")
            
            # Send notifications for updated deals
            for update in updated_deals:
                deal = update['deal']
                old_qty = update['old_quantity']
                new_qty = update['new_quantity']
                
                self.logger.info(f"Deal quantity updated: {deal['title']} ({old_qty} → {new_qty})")
                
                # Create batch ID for this specific update
                batch_id = f"update_{deal['deal_id']}_{current_time.strftime('%Y%m%d_%H%M%S')}"
                
                if not self.db.has_notification_been_sent(batch_id):
                    if self.notifier.send_deal_update_notification(deal, old_qty, new_qty):
                        self.db.mark_notification_sent(batch_id)
                        self.logger.info(f"Sent update notification for: {deal['title']}")
                    else:
                        self.logger.error(f"Failed to send update notification for: {deal['title']}")
            
            # Log completion
            log_check_complete(self.logger, len(new_deals), len(updated_deals))
            
            # Update last check time
            self.last_check_time = current_time
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"Error during deal check: {e}"
            log_error(self.logger, error_msg)
            
            # Send error notification
            try:
                self.notifier.send_error_notification(error_msg)
            except Exception as notify_error:
                self.logger.error(f"Failed to send error notification: {notify_error}")
    
    def get_status(self) -> Dict:
        """Get current status of the monitor."""
        return {
            'running': self.running,
            'health': self._get_health_status(),
            'config': {
                'check_interval_minutes': CHECK_INTERVAL_MINUTES,
                'auto_commit_enabled': AUTO_COMMIT_NEW_DEALS,
                'auto_commit_quantity': AUTO_COMMIT_QUANTITY,
                'log_level': LOG_LEVEL,
                'log_file': LOG_FILE
            }
        } 