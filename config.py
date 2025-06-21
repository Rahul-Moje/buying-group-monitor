import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug prints - only show if DEBUG environment variable is set
if os.getenv('DEBUG', 'false').lower() == 'true':
    print("DEBUG: Loading environment variables...")
    print(f"DEBUG: USERNAME from env: {os.getenv('BUYING_GROUP_USERNAME')}")
    print(f"DEBUG: PASSWORD from env: {'*' * len(os.getenv('BUYING_GROUP_PASSWORD', '')) if os.getenv('BUYING_GROUP_PASSWORD') else '(empty)'}")

# Buying Group Configuration
BUYING_GROUP_BASE_URL = "https://app.buyinggroup.ca"
BUYING_GROUP_LOGIN_URL = f"{BUYING_GROUP_BASE_URL}/login"
BUYING_GROUP_DASHBOARD_URL = f"{BUYING_GROUP_BASE_URL}/"

# Credentials (set these in .env file)
USERNAME = os.getenv('BUYING_GROUP_USERNAME')
PASSWORD = os.getenv('BUYING_GROUP_PASSWORD')

# Notification Configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Monitoring Configuration
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))  # Check every 5 minutes by default
DATABASE_PATH = os.getenv('DATABASE_PATH', 'buying_group_deals.db')

# Auto-commit Configuration
AUTO_COMMIT_NEW_DEALS = os.getenv('AUTO_COMMIT_NEW_DEALS', 'true').lower() == 'true'
AUTO_COMMIT_QUANTITY = int(os.getenv('AUTO_COMMIT_QUANTITY', '1'))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'buying_group_monitor.log')

# Network Configuration
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))  # 30 seconds timeout
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))  # Maximum retry attempts
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))  # Delay between retries in seconds

# User Agent to mimic browser
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"

# Headers for requests
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en-IN;q=0.7,en;q=0.6',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
} 