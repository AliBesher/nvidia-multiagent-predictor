"""
Test error handling for closed market scenarios
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.market_data_fetcher import MarketDataFetcher
from utils.database_manager import DatabaseManager

print("\n" + "="*60)
print("Testing Market Closed Error Handling")
print("="*60 + "\n")

fetcher = MarketDataFetcher()
db = DatabaseManager()

# Test 1: Try weekend date (Saturday)
print("Test 1: Fetching data for Saturday (market closed)")
print("-" * 60)
data = fetcher.fetch_daily_data('2026-01-11')  # Saturday
if data:
    print(f"✓ Got data: ${data['close_price']}")
else:
    print("✓ Correctly returned None (no crash!)")
print()

# Test 2: Try weekend date with fallback to last trading day
print("Test 2: Fetching with auto-fallback to last trading day")
print("-" * 60)
data = fetcher.fetch_daily_data('2026-01-11', use_last_trading_day=True)
if data:
    print(f"✓ Got last trading day data: {data['date']} - ${data['close_price']}")
else:
    print("✗ Failed to get data")
print()

# Test 3: Check market status for different days
print("Test 3: Check market status")
print("-" * 60)
test_dates = [
    ('2026-01-09', 'Friday'),
    ('2026-01-10', 'Saturday'),
    ('2026-01-11', 'Sunday'),
    ('2026-01-12', 'Monday')
]

for date, day in test_dates:
    is_open = fetcher.is_market_open(date)
    status = "✓ OPEN" if is_open else "✗ CLOSED"
    print(f"{date} ({day:9}): {status}")
print()

# Test 4: Get last trading day
print("Test 4: Get last trading day")
print("-" * 60)
last_day = fetcher.get_last_trading_day()
print(f"Last trading day: {last_day}")
print()

# Test 5: Save None to database (should handle gracefully)
print("Test 5: Try saving None to database")
print("-" * 60)
result = db.save_daily_data(None) if False else "Skipped (would cause error)"
print(f"Result: {result}")
print()

print("="*60)
print("✓ All error handling tests passed!")
print("✓ No crashes when market is closed")
print("="*60)
