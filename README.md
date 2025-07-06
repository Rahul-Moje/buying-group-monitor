# Buying Group Monitor

Monitor deals from the buying group website, store data in S3, and send notifications to Discord. Runs as a serverless container on AWS Lambda using ECR.

## Features
- Scrapes deals from the buying group site
- Stores data in S3 (JSON)
- Sends Discord notifications for new deals
- Runs on AWS Lambda as a container (ECR)

## Quick Deployment
1. Build and push Docker image to ECR
2. Create Lambda function from ECR image (via AWS Console)
3. Set environment variables (S3, credentials, Discord webhook)
4. Schedule with CloudWatch Events (every 5 minutes)

---

**See code comments for configuration and usage.** 