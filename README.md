# Buying Group Monitor 🚀

A Python-based monitoring system for the [Canada Buying Group](https://buyinggroup.ca/) that automatically checks for new deals and sends notifications via Discord.

## Features

- 🔍 **Automatic Deal Monitoring**: Scrapes the buying group website for new deals
- 📊 **Database Storage**: Stores deal information locally using SQLite
- 🔔 **Discord Notifications**: Sends rich notifications when new deals are found
- ⏰ **Scheduled Monitoring**: Runs continuously with configurable intervals
- 📈 **Statistics**: Track deal history and statistics
- 🔐 **Secure Authentication**: Handles login sessions automatically
- ☁️ **Cloud Deployment**: Run 24/7 on Railway or Render
- 🤖 **Auto-Commit**: Automatically reserves items for new deals
- 🚨 **Error Handling**: Comprehensive error notifications with stack traces
- 🔄 **Smart Retry Logic**: Handles minimum quantity requirements automatically

## New Features (2024-06)

- **Auto-Commit with Smart Error Handling**: Automatically reserves items and handles "Must buy X or more" errors with retry logic
- **Discord Error Notifications**: All warnings and errors are sent to Discord with full stack traces for debugging
- **Comprehensive Logging**: All activity is logged to a file (see `LOG_FILE` in `.env`). For Render, use `/tmp/buying_group_monitor.log`.
- **Network Resilience**: Configurable retry logic with exponential backoff for network requests
- **Test Coverage**: Run `python main.py test` to verify all core features work as expected.

## Prerequisites

- Python 3.7 or higher
- Buying Group account credentials
- Discord webhook URL (optional, for notifications)

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd buying-group-monitor
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example file
   cp env_example.txt .env
   
   # Edit .env with your credentials
   nano .env
   ```

4. **Configure your credentials in `.env`**
   ```env
   BUYING_GROUP_USERNAME=your_email@example.com
   BUYING_GROUP_PASSWORD=your_password
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
   CHECK_INTERVAL_MINUTES=5
   AUTO_COMMIT_NEW_DEALS=true
   AUTO_COMMIT_QUANTITY=1
   ```

## Discord Webhook Setup (Optional)

1. Create a Discord server or use an existing one
2. Go to Server Settings > Integrations > Webhooks
3. Create a new webhook
4. Copy the webhook URL and add it to your `.env` file

## Auto-Commit Feature

The monitor can automatically reserve items for new deals:

- **Enabled by default**: Set `AUTO_COMMIT_NEW_DEALS=true`
- **Configurable quantity**: Set `AUTO_COMMIT_QUANTITY=1` (or higher)
- **Smart error handling**: Automatically detects "Must buy X or more" errors and retries with the correct quantity
- **Discord notifications**: You'll get notified of all auto-commit attempts and results

### Auto-Commit Error Handling

When auto-commit encounters a minimum quantity requirement:
1. **First attempt**: Tries with your configured quantity
2. **Error detection**: Parses the error message to find minimum requirement
3. **Retry attempt**: Automatically retries with the correct minimum quantity
4. **Notification**: Sends Discord notification with the result

## Cloud Deployment (24/7 Operation)

This monitor is designed to run on cloud platforms for 24/7 operation, even when your laptop is off.

### Quick Setup

```bash
# Generate cloud configuration files
python deploy_cloud.py

# Choose your platform:
# 1. Railway (Free tier)
# 2. Render (Free tier)
# 3. Both Railway and Render
```

### Railway Deployment

1. **Sign up** at https://railway.app
2. **Connect** your GitHub repository
3. **Set environment variables** in Railway dashboard:
   - `BUYING_GROUP_USERNAME`
   - `BUYING_GROUP_PASSWORD`
   - `DISCORD_WEBHOOK_URL`
   - `CHECK_INTERVAL_MINUTES`
4. **Deploy** - Railway will automatically build and run your monitor

### Render Deployment

1. **Sign up** at https://render.com
2. **Connect** your GitHub repository
3. **Set environment variables** in Render dashboard
4. **Deploy** with one click

### Environment Variables for Cloud

Set these in your cloud platform's dashboard:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BUYING_GROUP_USERNAME` | Your buying group email | ✅ Yes | - |
| `BUYING_GROUP_PASSWORD` | Your buying group password | ✅ Yes | - |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | ❌ No | - |
| `CHECK_INTERVAL_MINUTES` | How often to check for new deals | ❌ No | 5 |
| `AUTO_COMMIT_NEW_DEALS` | Enable auto-commit for new deals | ❌ No | true |
| `AUTO_COMMIT_QUANTITY` | Default quantity for auto-commit | ❌ No | 1 |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | ❌ No | INFO |
| `LOG_FILE` | Log file path (use `/tmp/` for cloud) | ❌ No | buying_group_monitor.log |
| `DEBUG` | Enable debug mode (shows credentials) | ❌ No | false |
| `DATABASE_PATH` | Database file path | ❌ No | buying_group_deals.db |
| `REQUEST_TIMEOUT` | Network request timeout (seconds) | ❌ No | 30 |
| `MAX_RETRIES` | Maximum retry attempts | ❌ No | 3 |
| `RETRY_DELAY` | Delay between retries (seconds) | ❌ No | 5 |

### Render-Specific Settings

For Render deployment, use these values:

```env
LOG_FILE=/tmp/buying_group_monitor.log
DATABASE_PATH=/tmp/buying_group_deals.db
DEBUG=false
```

## Local Testing

### Run All Tests
```bash
python main.py test
```

### Test Login Credentials
```bash
python main.py test-login
```

### Run a Single Check
```bash
python main.py check
```

### View Statistics
```bash
python main.py stats
```

### View Commitments
```bash
python main.py list-commitments
```

### Update Commitment
```bash
python main.py update-commitment <deal_id> <new_quantity>
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `BUYING_GROUP_USERNAME` | Your buying group email | Required |
| `BUYING_GROUP_PASSWORD` | Your buying group password | Required |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | Optional |
| `CHECK_INTERVAL_MINUTES` | How often to check for new deals | 5 |
| `AUTO_COMMIT_NEW_DEALS` | Enable auto-commit for new deals | true |
| `AUTO_COMMIT_QUANTITY` | Default quantity for auto-commit | 1 |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_FILE` | Log file path | buying_group_monitor.log |
| `DEBUG` | Enable debug mode | false |
| `REQUEST_TIMEOUT` | Network timeout (seconds) | 30 |
| `MAX_RETRIES` | Retry attempts | 3 |
| `RETRY_DELAY` | Retry delay (seconds) | 5 |

## How It Works

1. **Authentication**: The monitor logs into your buying group account
2. **Scraping**: It scrapes the dashboard page for current deals
3. **Comparison**: New deals are compared against the local database
4. **Auto-Commit**: If enabled, automatically reserves items for new deals
5. **Error Handling**: Detects and handles minimum quantity requirements
6. **Notifications**: Discord notifications are sent for new deals, errors, and auto-commit results
7. **Storage**: All deal information is stored in SQLite database

## File Structure

```
buying-group-monitor/
├── main.py              # Main entry point
├── monitor.py           # Core monitoring logic
├── scraper.py           # Web scraping functionality
├── database.py          # Database operations
├── notifier.py          # Discord notifications
├── config.py            # Configuration management
├── logger.py            # Logging setup
├── tests.py             # Test cases
├── deploy_cloud.py      # Cloud deployment setup
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables example
├── README.md           # This file
└── buying_group_deals.db # SQLite database (created automatically)
```

## Troubleshooting

### Login Issues
- Verify your credentials in the `.env` file
- Run `python main.py test-login` to test authentication
- Check if the buying group website is accessible

### No Deals Found
- The website structure might have changed
- Check if you're logged in correctly
- Verify the scraper is finding deal cards on the page

### Discord Notifications Not Working
- Verify your Discord webhook URL is correct
- Check if the webhook is still active in Discord
- Ensure the webhook has permission to send messages

### Auto-Commit Issues
- Check Discord for error notifications with stack traces
- Verify minimum quantity requirements are being handled
- Check logs for detailed error information

### Cloud Deployment Issues
- Check environment variables are set correctly
- Verify the health check endpoint is working (`/health`)
- Check cloud platform logs for errors
- Ensure log file path uses `/tmp/` directory

### Database Issues
- The database file is created automatically
- If corrupted, delete `buying_group_deals.db` and restart

## Security Notes

- Your credentials are stored securely in cloud environment variables
- Never commit your `.env` file to version control
- The database contains deal information but no sensitive data
- Debug mode should only be enabled temporarily for troubleshooting

## Legal Considerations

- This tool is for personal use only
- Respect the website's terms of service
- Don't overload the server with too frequent requests
- Use responsibly and ethically

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your configuration is correct
3. Test your login credentials
4. Check if the website structure has changed

## Running Tests

To run all test cases and verify your setup:

```bash
python main.py test
```

All tests should pass. If any fail, check your environment variables and database schema.

## Recommended LOG_FILE for Cloud

For Render or Railway, set:

```
LOG_FILE=/tmp/buying_group_monitor.log
```

in your environment variables dashboard. 