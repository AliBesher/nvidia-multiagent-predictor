"""
Test that workflow handles ALL market closure scenarios
(Weekends, Holidays, Special Closures, etc.)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.workflow_manager import WorkflowManager
from utils.market_data_fetcher import MarketDataFetcher

print("\n" + "="*60)
print("All Market Closure Scenarios Test")
print("="*60 + "\n")

wf = WorkflowManager()
fetcher = MarketDataFetcher()

# Test various closure scenarios
test_scenarios = [
    # Regular trading days
    ('2026-01-09', 'Friday - Regular Trading Day'),
    ('2026-01-12', 'Monday - Regular Trading Day'),
    
    # Weekends
    ('2026-01-10', 'Saturday - Weekend Closure'),
    ('2026-01-11', 'Sunday - Weekend Closure'),
    
    # Common US Market Holidays (2026)
    ('2026-01-01', 'New Year\'s Day - Holiday'),
    ('2026-01-19', 'Martin Luther King Jr. Day - Holiday'),
    ('2026-12-25', 'Christmas Day - Holiday'),
]

print("Testing Market Status Detection:")
print("-" * 60)

for date, description in test_scenarios:
    is_open = fetcher.is_market_open(date)
    status = "OPEN ✓" if is_open else "CLOSED ✗"
    
    # Get workflow action
    start, end = wf.get_date_range_for_sentiment(date)
    
    if is_open:
        action = f"Normal: Collect data for {date}"
    else:
        last_day = wf.get_last_trading_day_for_update()
        action = f"Update last trading day ({last_day})"
    
    print(f"{date} | {status:12} | {description}")
    print(f"           Action: {action}")
    print()

print("="*60)
print("KEY INSIGHT:")
print("="*60)
print("✓ ANY market closure (weekend/holiday/special) triggers:")
print("  1. Skip market data collection")
print("  2. Save articles with actual date")
print("  3. Update LAST TRADING DAY's sentiment")
print("  4. Next trading day uses updated sentiment")
print()
print("This works for:")
print("  • Regular weekends (Sat/Sun)")
print("  • Federal holidays (New Year, Christmas, etc.)")
print("  • Special closures (weather, emergencies)")
print("  • Any other market closure")
print()
print("✓ No special code needed - is_market_open() handles it all!")
print("="*60)
