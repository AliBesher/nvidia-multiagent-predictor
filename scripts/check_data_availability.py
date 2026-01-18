"""
Check yfinance data availability and update timing
"""
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

print("\n" + "="*60)
print("Yahoo Finance Data Availability Check")
print("="*60 + "\n")

nvda = yf.Ticker("NVDA")

# Get last 10 days of data
df = nvda.history(period="10d")

if not df.empty:
    df.index = df.index.tz_localize(None)
    
    print(f"📅 Today's Date: {datetime.now().strftime('%Y-%m-%d %A')}")
    print(f"📊 Latest Data Available: {df.index[-1].strftime('%Y-%m-%d %A')}\n")
    
    print("Last 5 trading days:")
    print("-" * 60)
    for idx in df.tail(5).index:
        row = df.loc[idx]
        print(f"{idx.strftime('%Y-%m-%d %A'):25} | Close: ${row['Close']:.2f} | Vol: {int(row['Volume']):,}")
    
    # Check if today's data is available
    today = datetime.now().date()
    latest = df.index[-1].date()
    
    print("\n" + "="*60)
    print("DATA UPDATE INFO:")
    print("="*60)
    print(f"✓ Yahoo Finance updates AFTER market close (4:00 PM ET)")
    print(f"✓ Data is typically available 15-30 minutes after close")
    print(f"✓ Weekend/Holiday data is NOT available")
    print(f"\nLatest available: {latest}")
    print(f"Today's date: {today}")
    
    if latest == today:
        print(f"\n✓ TODAY'S DATA IS AVAILABLE!")
    elif latest == (today - timedelta(days=1)):
        print(f"\n⚠ Yesterday's data is latest (today might not be closed yet)")
    else:
        days_behind = (today - latest).days
        print(f"\n⚠ Data is {days_behind} days behind (weekend or market closed)")
    
    print("\n" + "="*60)
else:
    print("❌ No data available")
