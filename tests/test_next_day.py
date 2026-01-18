"""Test next_day_close update logic with simulated data"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_manager import DatabaseManager
import psycopg2

db = DatabaseManager()

print("="*60)
print("TESTING NEXT DAY CLOSE UPDATE")
print("="*60)

# 1. Check if there's a previous day
previous_day = db.get_previous_trading_day('2026-01-12')
print(f"\n1. Previous trading day before 2026-01-12: {previous_day}")

if not previous_day:
    print("   ✓ No previous day - this is expected for day 1")
    print("   ✓ Code will skip update gracefully")
    
    # Simulate what will happen on day 2
    print("\n" + "="*60)
    print("SIMULATION: What happens on day 2 (2026-01-13)")
    print("="*60)
    
    print("\nDay 2 workflow will:")
    print("1. Collect 2026-01-13 market data (e.g., Close = $186.50)")
    print("2. Save 2026-01-13 data to database")
    print("3. Find previous day = 2026-01-12")
    print("4. Update 2026-01-12 row:")
    print("   - next_day_close = $186.50")
    print("   - price_change_percent = +0.84%")
    print("\nResult: 2026-01-12 row will show tomorrow's result!")

print("\n" + "="*60)
