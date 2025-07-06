# ECR + Lambda Deployment Guide

## Prerequisites

1. **AWS CLI configured** with your IAM user credentials
2. **Docker installed** and running
3. **ECR repository created** (or will be created during deployment)

## Deployment Steps

### Step 1: Push to ECR (CLI)

#### 1. Configure AWS CLI
```bash
aws configure
# Enter your IAM user credentials:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region (us-east-1)
# - Default output format (json)
```

#### 2. Set Environment Variables
```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
export ECR_REPOSITORY=buying-group-monitor
export IMAGE_TAG=latest
```

#### 3. Build and Push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Create repository
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION --image-scanning-configuration scanOnPush=true --encryption-configuration encryptionType=AES256

# Build and tag
docker build -t buying-group-monitor .
docker tag buying-group-monitor:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
```

### Step 2: Configure Lambda (Console)

1. **Go to Lambda Console**: https://console.aws.amazon.com/lambda/
2. **Click "Create function"**
3. **Choose "Container image"**
4. **Fill in details**:
   - Function name: `buying-group-monitor`
   - Container image URI: `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/buying-group-monitor:latest`
   - Architecture: `x86_64`
   - **Execution role**: Create new role with basic Lambda permissions
5. **Click "Create function"**

#### Configure Environment Variables
1. Go to **Configuration → Environment variables**
2. Add these variables:
   - `S3_BUCKET`: `buying-group-deals`
   - `BUYING_GROUP_USERNAME`: Your username
   - `BUYING_GROUP_PASSWORD`: Your password
   - `DISCORD_WEBHOOK_URL`: Your Discord webhook (optional)

#### Configure Function Settings
1. Go to **Configuration → General configuration**
2. Set:
   - Timeout: `5 minutes`
   - Memory: `512 MB`

#### Set Up Scheduling
1. Go to **Configuration → Triggers**
2. Click **Add trigger**
3. Choose **EventBridge (CloudWatch Events)**
4. **Rule**: Create a new rule
5. **Rule name**: `buying-group-monitor-rule`
6. **Rule type**: Schedule expression
7. **Schedule expression**: `rate(5 minutes)`
8. Click **Add**

## Environment Variables

Set these in your Lambda function configuration:

- `S3_BUCKET`: `buying-group-deals`
- `BUYING_GROUP_USERNAME`: Your username
- `BUYING_GROUP_PASSWORD`: Your password
- `DISCORD_WEBHOOK_URL`: Your Discord webhook (optional)

## Scheduling

The deployment script automatically creates a CloudWatch Events rule to trigger the Lambda every 5 minutes.

## Troubleshooting

### Common Issues:

1. **Authentication Error**: Make sure your IAM user has ECR + Lambda permissions
2. **Build Failures**: Check Dockerfile and dependencies
3. **Lambda Timeout**: Increase timeout in Lambda configuration
4. **Memory Issues**: Increase memory allocation

### Required IAM Permissions:

Your IAM user needs these policies:
- `AmazonEC2ContainerRegistryFullAccess`
- `AWSLambda_FullAccess`
- `AmazonS3FullAccess`
- `CloudWatchLogsFullAccess`
- `IAMReadOnlyAccess`

## Cost Considerations

- ECR storage: ~$0.10 per GB per month
- Lambda: Free tier includes 1M requests/month
- S3: ~$0.023 per GB per month
- Estimated total: < $5/month for small usage

## Monitoring

- Check CloudWatch logs for Lambda execution
- Monitor S3 bucket for deal data
- Set up CloudWatch alarms for errors 