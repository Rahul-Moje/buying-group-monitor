# Buying Group Monitor 🚀

A Python-based monitoring system for the [Canada Buying Group](https://buyinggroup.ca/) and other deal/auction sites. It automatically checks for new deals and sends notifications via Discord.

## Features

- 🔍 **Automatic Deal Monitoring**: Scrapes supported websites for new deals
- 📊 **Database Storage**: Stores deal information locally using SQLite
- 🔔 **Discord Notifications**: Sends rich notifications when new deals or updates are found
- ⏰ **Scheduled Monitoring**: Runs continuously with configurable intervals
- 📈 **Statistics**: Track deal history and statistics
- 🔒 **Secure Authentication**: Handles login sessions automatically
- ☁️ **Cloud Deployment**: Run 24/7 on Railway or Render
- 🧩 **Modular Scraper System**: Easily add support for new sites (e.g., 2ndTurn, more)
- 🚨 **Error Handling**: Comprehensive error notifications with stack traces
- 🔄 **Smart Retry Logic**: Handles network issues with retry and backoff

## New Features (2024-06)

- **Modular Scraper Support**: Easily add new sites by implementing a new scraper class.
- **Discord Error Notifications**: All warnings and errors are sent to Discord with full stack traces for debugging
- **Comprehensive Logging**: All activity is logged to a file (see `LOG_FILE` in `.env`). For Render, use `/tmp/buying_group_monitor.log`.
- **Network Resilience**: Configurable retry logic with exponential backoff for network requests

## Prerequisites

- Python 3.7 or higher
- Buying Group account credentials (or credentials for other supported sites)
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
   ```

## Discord Webhook Setup (Optional)

1. Create a Discord server or use an existing one
2. Go to Server Settings > Integrations > Webhooks
3. Create a new webhook
4. Copy the webhook URL and add it to your `.env` file

## Cloud Deployment (24/7 Operation)

This monitor is designed to run on cloud platforms for 24/7 operation, even when your laptop is off.

### Recommended: Render or Railway

- **Render**: Easiest for most users. Supports background workers, persistent storage, and has a free tier. Your project includes a `render.yaml` for one-click deployment.
- **Railway**: Also easy, with a generous free tier and GitHub integration.

#### Quick Setup (Render Example)
```bash
# Push your code to GitHub
# Go to https://render.com, create a new service, and connect your repo
# Render will detect your render.yaml and set up the service
# Set your environment variables in the dashboard
# Deploy!
```

### Environment Variables for Cloud

Set these in your cloud platform's dashboard:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BUYING_GROUP_USERNAME` | Your buying group email | ✅ Yes | - |
| `BUYING_GROUP_PASSWORD` | Your buying group password | ✅ Yes | - |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | ❌ No | - |
| `CHECK_INTERVAL_MINUTES` | How often to check for new deals | ❌ No | 5 |
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

## Local Usage

### Start the Monitor
```bash
python main.py start
```

### Check Monitor Status
```bash
python main.py status
```

## Health and Status Endpoints
- **/health**: Returns JSON with service health status (port 8000 by default)
- **/status**: Returns JSON with current monitor status and config
- You can change the port with `--port`, e.g. `python main.py start --port 9000`

## Notification Logic
- **You will only receive Discord notifications when:**
  - New deals are detected (not previously seen)
  - Existing deals have a quantity update
- **No notification is sent if nothing changes** (no spam)

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `BUYING_GROUP_USERNAME` | Your buying group email | Required |
| `BUYING_GROUP_PASSWORD` | Your buying group password | Required |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | Optional |
| `CHECK_INTERVAL_MINUTES` | How often to check for new deals | 5 |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_FILE` | Log file path | buying_group_monitor.log |
| `DEBUG` | Enable debug mode | false |
| `REQUEST_TIMEOUT` | Network timeout (seconds) | 30 |
| `MAX_RETRIES` | Retry attempts | 3 |
| `RETRY_DELAY` | Retry delay (seconds) | 5 |

## How It Works

1. **Authentication**: The monitor logs into your buying group account (or other supported site)
2. **Scraping**: It scrapes the dashboard page for current deals using the appropriate scraper
3. **Comparison**: New deals are compared against the local database
4. **Notifications**: Discord notifications are sent for new deals and updates
5. **Storage**: All deal information is stored in SQLite database

## Extending to New Sites
- Implement a new scraper class for the target site (see `scraper.py` for an example)
- Register the new scraper in the monitor
- Ensure the new scraper returns deals in the standard format
- Update config/CLI to allow selecting the site

## File Structure

```
buying-group-monitor/
├── main.py              # Main entry point
├── monitor.py           # Core monitoring logic
├── scraper.py           # Web scraping functionality (modular)
├── database.py          # Database operations
├── notifier.py          # Discord notifications
├── config.py            # Configuration management
├── logger.py            # Logging setup
├── deploy_cloud.py      # Cloud deployment setup
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables example
├── README.md           # This file
└── buying_group_deals.db # SQLite database (created automatically)
```

## Troubleshooting

### Login Issues
- Verify your credentials in the `.env` file
- Check if the buying group website is accessible
- Ensure your account is active and not locked

### No Deals Found
- The website structure might have changed
- Check if you're logged in correctly
- Verify the scraper is finding deal cards on the page

### Discord Notifications Not Working
- Verify your Discord webhook URL is correct
- Check if the webhook is still active in Discord
- Ensure the webhook has permission to send messages

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

## Recommended LOG_FILE for Cloud

For Render or Railway, set:

```
LOG_FILE=/tmp/buying_group_monitor.log
```

in your environment variables dashboard. 