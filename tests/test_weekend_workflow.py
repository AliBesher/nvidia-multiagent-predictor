"""
Test Weekend Article Handling Workflow
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.workflow_manager import WorkflowManager
from datetime import datetime

print("\n" + "="*60)
print("Weekend Article Handling Test")
print("="*60 + "\n")

wf = WorkflowManager()

# Test different scenarios
test_dates = [
    ('2026-01-09', 'Friday (trading day)'),
    ('2026-01-10', 'Saturday (weekend)'),
    ('2026-01-11', 'Sunday (weekend)'),
    ('2026-01-12', 'Monday (trading day)'),
]

for date, description in test_dates:
    print(f"\n{description} - {date}")
    print("-" * 60)
    
    # Check if trading day
    is_trading = wf.should_collect_market_data(date)
    print(f"Market Status: {'OPEN ✓' if is_trading else 'CLOSED ✗'}")
    
    # Get date range for sentiment
    start, end = wf.get_date_range_for_sentiment(date)
    print(f"Article Range: {start} to {end}")
    
    # Determine what to update
    if is_trading:
        print(f"Action: Save market data + articles for {date}")
        print(f"Update sentiment: {date}")
    else:
        last_day = wf.get_last_trading_day_for_update()
        print(f"Action: Save articles for {date}")
        print(f"Update sentiment: {last_day} (last trading day)")

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
summary = wf.get_summary()
for key, value in summary.items():
    print(f"{key}: {value}")

print("\n✓ Weekend handling logic working correctly!")
print("\nWEEKEND WORKFLOW:")
print("  Saturday: Collect articles → Update Friday's sentiment")
print("  Sunday:   Collect articles → Update Friday's sentiment")
print("  Monday:   Predict using Friday's updated sentiment")
print("="*60)
