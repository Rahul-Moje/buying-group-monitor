#!/usr/bin/env python3
"""
Setup script for Buying Group Monitor
"""

import os
import shutil
from pathlib import Path

def main():
    print("🚀 Setting up Buying Group Monitor...")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        if os.path.exists('env_example.txt'):
            print("📝 Creating .env file from template...")
            shutil.copy('env_example.txt', '.env')
            print("✅ Created .env file")
            print("⚠️  Please edit .env file with your credentials before running the monitor")
        else:
            print("❌ env_example.txt not found")
            return False
    else:
        print("✅ .env file already exists")
    
    # Check if requirements are installed
    try:
        import requests
        import bs4  # beautifulsoup4
        import schedule
        import dotenv
        print("✅ All required packages are installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("📦 Installing requirements...")
        os.system("pip install --user -r requirements.txt")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your credentials")
    print("2. Test login: python main.py test-login")
    print("3. Start monitoring: python main.py start")
    
    return True

if __name__ == "__main__":
    main() 