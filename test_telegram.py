#!/usr/bin/env python3
"""
Simple Telegram Bot Token Tester
Test if your bot token is valid and can connect to Telegram
"""

import sys
from dotenv import load_dotenv
import os
import requests

# Load environment
load_dotenv('.env')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def test_bot_token():
    """Test if bot token is valid"""
    print(f"Testing bot token: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Bot token VALID!")
                print(f"   Bot name: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                return True
            else:
                print(f"❌ Bot token INVALID: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("This could be:")
        print("  - Network/firewall blocking Telegram")
        print("  - Invalid bot token")
        print("  - Internet connection issues")
        return False

if __name__ == "__main__":
    try:
        result = test_bot_token()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test cancelled")
        sys.exit(1)