#!/usr/bin/env python3
"""
Buying Group Monitor - Core Monitoring Logic
"""

import time
import logging
from typing import Dict, Any
from scraper import BuyingGroupScraper
from notifier import DiscordNotifier
from database import DealDatabase
from config import (
    CHECK_INTERVAL_MINUTES,
    USERNAME,
    PASSWORD,
    DISCORD_WEBHOOK_URL,
    S3_BUCKET,
    S3_KEY
)
from logger import setup_logger

class BuyingGroupMonitor:
    def __init__(self):
        self.logger = setup_logger('buying_group_monitor')
        self.running = False
        self.scraper = BuyingGroupScraper()
        self.notifier = DiscordNotifier(DISCORD_WEBHOOK_URL) if DISCORD_WEBHOOK_URL else None
        self.db = DealDatabase(bucket=S3_BUCKET, key=S3_KEY)
        
    def start(self):
        """Start the monitoring loop."""
        self.running = True
        self.logger.info("Starting Buying Group Monitor...")
        
        # Send startup notification
        if self.notifier:
            self.notifier.send_startup_notification()
        
        while self.running:
            try:
                self.check_for_new_deals()
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retrying
        
        self.logger.info("Buying Group Monitor stopped")
    
    def stop(self):
        """Stop the monitoring loop."""
        self.running = False
        self.logger.info("Stopping Buying Group Monitor...")
    
    def check_for_new_deals(self):
        """Check for new deals and send notifications."""
        try:
            self.logger.info("Checking for new deals...")
            
            # Get current deals from website
            current_deals = self.scraper.get_deals()
            
            # Find new deals
            new_deals = []
            for deal in current_deals:
                if not self.db.deal_exists(deal['deal_id']):
                    new_deals.append(deal)
                    self.db.add_deal(deal)
            
            if new_deals:
                self.logger.info(f"Found {len(new_deals)} new deals")
                if self.notifier:
                    self.notifier.send_new_deals_notification(new_deals)
            else:
                self.logger.info("No new deals found")
                
        except Exception as e:
            self.logger.error(f"Error checking for new deals: {e}", exc_info=True)
            if self.notifier:
                self.notifier.send_error_notification(str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the monitor."""
        try:
            return {
                'running': self.running,
                'health': 'healthy' if self.running else 'stopped',
                'config': {
                    'check_interval_minutes': CHECK_INTERVAL_MINUTES,
                    's3_bucket': S3_BUCKET,
                    'discord_webhook_configured': bool(DISCORD_WEBHOOK_URL)
                },
                'database_stats': self.db.get_database_stats()
            }
        except Exception as e:
            return {
                'running': self.running,
                'health': 'error',
                'error': str(e)
            } 