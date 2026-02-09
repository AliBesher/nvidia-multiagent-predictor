"""
Test script to verify market data fetcher and database manager
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database_manager import DatabaseManager
from data.market_data_fetcher import MarketDataFetcher
from datetime import datetime, timedelta

def test_database_integration():
    """Test fetching stock data and saving to database"""
    
    print("\n" + "="*60)
    print("Testing Market Data Fetcher + Database Manager")
    print("="*60 + "\n")
    
    # Initialize components
    db = DatabaseManager()
    fetcher = MarketDataFetcher()
    
    # Use January 9, 2026 (Thursday) - known good date
    date = '2026-01-09'
    print(f"📅 Testing with date: {date}\n")
    
    # Fetch market data
    print("📊 Fetching NVIDIA stock data...")
    data = fetcher.fetch_daily_data(date)
    
    if not data:
        print("❌ Failed to fetch market data")
        return
    
    print(f"✓ Fetched data successfully!")
    print(f"   Close Price: ${data['close_price']}")
    print(f"   Volume: {data['volume']:,}")
    print(f"   RSI: {data.get('rsi', 'N/A')}")
    print()
    
    # Save to database
    print("💾 Saving to database...")
    success = db.save_daily_data(data)
    
    if success:
        print("✓ Data saved successfully!\n")
    else:
        print("❌ Failed to save data\n")
        return
    
    # Verify by retrieving
    print("🔍 Verifying data...")
    retrieved = db.get_daily_data(date)
    
    if retrieved:
        print(f"✓ Data retrieved successfully!")
        print(f"   Date: {retrieved['date']}")
        print(f"   Close: ${retrieved['close_price']}")
    else:
        print("❌ Failed to retrieve data")
        return
    
    # Get total count
    count = db.get_data_count()
    print(f"\n📈 Total records in database: {count}")
    
    # Clean up test data
    print("\n🧹 Cleaning up test data...")
    import psycopg2
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_data WHERE date = %s", (date,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✓ Deleted test data for {date}")
    
    print("\n" + "="*60)
    print("✓ All tests passed! Database cleaned.")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_database_integration()
