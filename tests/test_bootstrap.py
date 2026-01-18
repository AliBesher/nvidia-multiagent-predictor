"""Test bootstrap logic for empty database on weekend"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ['TESTING'] = 'true'

from utils.database_manager import DatabaseManager
from utils.market_data_fetcher import MarketDataFetcher
from datetime import datetime

# Initialize
db = DatabaseManager()
fetcher = MarketDataFetcher()

print("="*60)
print("BOOTSTRAP LOGIC TEST")
print("="*60)

# Check current database state
data_count = db.get_data_count()
print(f"\nCurrent database rows: {data_count}")

# Simulate weekend check
test_date = "2026-01-11"  # Saturday
is_market_open = fetcher.is_market_open(test_date)
print(f"Market open on {test_date}? {is_market_open}")

# Get last trading day
last_trading_day = fetcher.get_last_trading_day()
print(f"\nLast trading day from Yahoo: {last_trading_day}")

# Check if we have data for it
existing_data = db.get_daily_data(last_trading_day)
print(f"Data exists for {last_trading_day}? {existing_data is not None}")

if existing_data:
    print(f"  Close: ${existing_data['close_price']:.2f}")
    print(f"  Volume: {existing_data['volume']:,}")

print("\n" + "="*60)
print("BOOTSTRAP LOGIC:")
print("="*60)
print(f"1. Database empty? {data_count == 0}")
print(f"2. Market closed? {not is_market_open}")
print(f"3. Bootstrap needed? {data_count == 0 and not is_market_open}")

if data_count == 0 and not is_market_open:
    print(f"\n✓ Would bootstrap with {last_trading_day} data")
else:
    print("\n✓ No bootstrap needed - normal flow")

print("="*60)
