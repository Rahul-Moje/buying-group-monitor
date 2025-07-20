# Buying Group Monitor

A Python-based monitor for scraping and tracking deals from buyinggroup.ca, with AWS S3 and Discord integration.

## Features
- Scrapes deals from buyinggroup.ca
- Stores data in AWS S3
- Sends notifications to Discord
- Docker and AWS Lambda compatible

## Setup
1. **Clone the repo:**
   ```sh
   git clone <your-repo-url>
   cd buying-group
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Set environment variables:**
   - `BUYING_GROUP_USERNAME` (your login email)
   - `BUYING_GROUP_PASSWORD` (your password)
   - `DISCORD_WEBHOOK_URL` (for notifications)
   - `S3_BUCKET` (your S3 bucket name)
   - `S3_KEY` (optional, default: deals.json)

   You can use a `.env` file or set them in your environment.

4. **Run locally:**
   ```sh
   python main.py start
   ```

5. **Docker:**
   ```sh
   docker build -t buying-group .
   # Set env vars as needed
   docker run --env-file .env buying-group
   ```

## Security
- **No credentials are stored in the codebase.**
- Never commit your `.env` or any secrets to version control.

## License
MIT 