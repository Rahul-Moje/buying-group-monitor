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
   ```

## Discord Webhook Setup (Optional)

1. Create a Discord server or use an existing one
2. Go to Server Settings > Integrations > Webhooks
3. Create a new webhook
4. Copy the webhook URL and add it to your `.env` file

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

| Variable | Description | Required |
|----------|-------------|----------|
| `BUYING_GROUP_USERNAME` | Your buying group email | ✅ Yes |
| `BUYING_GROUP_PASSWORD` | Your buying group password | ✅ Yes |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | ❌ No |
| `CHECK_INTERVAL_MINUTES` | How often to check for new deals | ❌ No (default: 5) |

## Local Testing

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

## How It Works

1. **Authentication**: The monitor logs into your buying group account
2. **Scraping**: It scrapes the dashboard page for current deals
3. **Comparison**: New deals are compared against the local database
4. **Notifications**: Discord notifications are sent for new deals, quantity changes, and commitment updates
5. **Storage**: All deal information is stored in SQLite database

## File Structure

```
buying-group-monitor/
├── main.py              # Main entry point
├── monitor.py           # Core monitoring logic
├── scraper.py           # Web scraping functionality
├── database.py          # Database operations
├── notifier.py          # Discord notifications
├── config.py            # Configuration management
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

### Cloud Deployment Issues
- Check environment variables are set correctly
- Verify the health check endpoint is working (`/health`)
- Check cloud platform logs for errors

### Database Issues
- The database file is created automatically
- If corrupted, delete `buying_group_deals.db` and restart

## Security Notes

- Your credentials are stored securely in cloud environment variables
- Never commit your `.env` file to version control
- The database contains deal information but no sensitive data
- All communication with the buying group website uses HTTPS

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