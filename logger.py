import logging
import os
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE

def setup_logger(name: str = 'buying_group_monitor') -> logging.Logger:
    """Set up a logger with file and console handlers."""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_monitoring_start(logger: logging.Logger):
    """Log monitoring session start."""
    logger.info("🚀 Buying Group Monitor started")
    logger.info(f"Check interval: {os.getenv('CHECK_INTERVAL_MINUTES', '5')} minutes")
    logger.info(f"Auto-commit enabled: {os.getenv('AUTO_COMMIT_NEW_DEALS', 'true')}")
    logger.info(f"Auto-commit quantity: {os.getenv('AUTO_COMMIT_QUANTITY', '1')}")

def log_check_start(logger: logging.Logger):
    """Log the start of a monitoring check."""
    logger.info("🔍 Starting monitoring check...")

def log_check_complete(logger: logging.Logger, new_deals: int, updated_deals: int):
    """Log the completion of a monitoring check."""
    if new_deals > 0 or updated_deals > 0:
        logger.info(f"✅ Check complete: {new_deals} new deals, {updated_deals} updated deals")
    else:
        logger.info("✅ Check complete: No new deals or updates found")

def log_new_deal(logger: logging.Logger, deal: dict):
    """Log a new deal found."""
    logger.info(f"🆕 New deal found: {deal['title']} (ID: {deal['deal_id']})")
    logger.info(f"   Store: {deal['store']}")
    logger.info(f"   Price: ${deal['price']:.2f}")
    logger.info(f"   Max Quantity: {deal['max_quantity']}")

def log_existing_deal(logger: logging.Logger, deal: dict):
    """Log an existing deal found."""
    logger.debug(f"📋 Existing deal: {deal['title']} (ID: {deal['deal_id']})")

def log_quantity_update(logger: logging.Logger, deal: dict, old_qty: int, new_qty: int):
    """Log a quantity update."""
    logger.info(f"📊 Quantity updated for {deal['title']}: {old_qty} → {new_qty}")

def log_commitment_update(logger: logging.Logger, deal: dict, old_commit: int, new_commit: int):
    """Log a commitment update."""
    logger.info(f"📝 Commitment updated for {deal['title']}: {old_commit} → {new_commit}")

def log_auto_commit(logger: logging.Logger, deal: dict, quantity: int):
    """Log automatic commitment."""
    logger.info(f"🤖 Auto-committed {quantity} item(s) for {deal['title']}")

def log_error(logger: logging.Logger, error: str, context: str = ""):
    """Log an error."""
    if context:
        logger.error(f"❌ Error in {context}: {error}")
    else:
        logger.error(f"❌ Error: {error}")

def log_discord_notification(logger: logging.Logger, notification_type: str, success: bool):
    """Log Discord notification status."""
    if success:
        logger.info(f"📨 Discord {notification_type} notification sent successfully")
    else:
        logger.error(f"📨 Failed to send Discord {notification_type} notification") 