#!/usr/bin/env python3
"""
Cloud Deployment Script for Buying Group Monitor
Deploy to Railway or Render for 24/7 operation
"""

import os
import sys
from pathlib import Path

def create_railway_config():
    """Create Railway configuration files."""
    
    # Create railway.json
    railway_config = {
        "$schema": "https://railway.app/railway.schema.json",
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python main.py start",
            "healthcheckPath": "/health",
            "healthcheckTimeout": 300,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    with open('railway.json', 'w') as f:
        import json
        json.dump(railway_config, f, indent=2)
    
    # Create Procfile for Railway
    with open('Procfile', 'w') as f:
        f.write('web: python main.py start\n')
    
    print("✅ Railway configuration files created!")

def create_render_config():
    """Create Render configuration files."""
    
    # Create render.yaml
    render_config = """
services:
  - type: web
    name: buying-group-monitor
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py start
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.0
    healthCheckPath: /health
    autoDeploy: true
"""
    
    with open('render.yaml', 'w') as f:
        f.write(render_config)
    
    print("✅ Render configuration files created!")

def main():
    print("🚀 Cloud Deployment Setup for Buying Group Monitor")
    print("=" * 50)
    print()
    print("Choose your cloud deployment option:")
    print("1. Railway (Free tier available)")
    print("2. Render (Free tier available)")
    print("3. Both Railway and Render")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        create_railway_config()
    elif choice == "2":
        create_render_config()
    elif choice == "3":
        create_railway_config()
        create_render_config()
    else:
        print("Invalid choice!")
        return
    
    print()
    print("📋 Next Steps:")
    print("1. Set up your environment variables in the cloud platform")
    print("2. Deploy your code to the chosen platform")
    print("3. The monitor will run 24/7 even when your laptop is off!")
    print()
    print("🔧 Environment Variables to set:")
    print("   - BUYING_GROUP_USERNAME")
    print("   - BUYING_GROUP_PASSWORD") 
    print("   - DISCORD_WEBHOOK_URL")
    print("   - CHECK_INTERVAL_MINUTES")
    print()
    print("🌐 Deployment URLs:")
    print("   Railway: https://railway.app")
    print("   Render: https://render.com")

if __name__ == "__main__":
    main() 