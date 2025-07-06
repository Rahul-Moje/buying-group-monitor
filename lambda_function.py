import json
import boto3
import os
from datetime import datetime
import logging
from database import DealDatabase
from scraper import BuyingGroupScraper
from notifier import DiscordNotifier

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to monitor buying group deals
    """
    try:
        logger.info("Starting buying group monitor...")
        
        # Get configuration from environment variables
        bucket_name = os.environ.get('S3_BUCKET', 'buying-group-deals')
        username = os.environ.get('BUYING_GROUP_USERNAME')
        password = os.environ.get('BUYING_GROUP_PASSWORD')
        discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')
        
        if not all([bucket_name, username, password]):
            raise ValueError("Missing required environment variables")
        
        # Initialize components
        db = DealDatabase(bucket=bucket_name, key='deals.json')
        scraper = BuyingGroupScraper()
        notifier = DiscordNotifier(discord_webhook) if discord_webhook else None
        
        # Check for new deals
        new_deals = check_for_new_deals(scraper, db)
        
        if new_deals:
            # Send Discord notification
            if notifier:
                notifier.send_new_deals_notification(new_deals)
            
            logger.info(f"Found {len(new_deals)} new deals")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Found {len(new_deals)} new deals',
                    'deals': new_deals
                })
            }
        else:
            logger.info("No new deals found")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No new deals found'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def check_for_new_deals(scraper, db):
    """
    Check for new deals using the scraper and save to database
    """
    try:
        # Get current deals from website
        current_deals = scraper.get_deals()
        
        # Get existing deals from database
        existing_deals = db.get_all_deals()
        
        # Find new deals
        new_deals = []
        for deal in current_deals:
            if not db.deal_exists(deal['deal_id']):
                new_deals.append(deal)
                db.add_deal(deal)
        
        return new_deals
        
    except Exception as e:
        logger.error(f"Error checking for new deals: {str(e)}")
        return [] 