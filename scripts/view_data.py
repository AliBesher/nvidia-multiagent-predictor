"""Quick script to view today's data from database"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_manager import DatabaseManager
from datetime import datetime

db = DatabaseManager()

# Get today's market data
data = db.get_daily_data('2026-01-12')

print("\n" + "="*60)
print("MARKET DATA FOR 2026-01-12")
print("="*60)
print(f"Date:           {data['date']}")
print(f"Close:          ${data['close_price']:.2f}")
print(f"Open:           ${data['open_price']:.2f}")
print(f"High:           ${data['high_price']:.2f}")
print(f"Low:            ${data['low_price']:.2f}")
print(f"Volume:         {data['volume']:,}")
print(f"\nTechnical Indicators:")
print(f"RSI:            {data['rsi']:.2f}" if data.get('rsi') else "RSI:            N/A")
print(f"MACD:           {data['macd']:.4f}" if data.get('macd') else "MACD:           N/A")
print(f"MACD Signal:    {data['macd_signal']:.4f}" if data.get('macd_signal') else "MACD Signal:    N/A")
print(f"MA (50-day):    ${data['moving_avg_50']:.2f}" if data.get('moving_avg_50') else "MA (50-day):    N/A")
print(f"MA (200-day):   ${data['moving_avg_200']:.2f}" if data.get('moving_avg_200') else "MA (200-day):   N/A")
print(f"\nSentiment:      {data['sentiment_score']:.2f}/100" if data.get('sentiment_score') else "\nSentiment:      N/A")

# Get articles
articles = db.get_articles_for_date('2026-01-12')

print("\n" + "="*60)
print(f"NEWS ARTICLES ({len(articles)} total)")
print("="*60)

for i, article in enumerate(articles, 1):
    print(f"\n{i}. [{article.get('source', 'Unknown')}] {article['title']}")
    print(f"   Date: {article['date']}")
    print(f"   URL: {article['url'][:80] if article.get('url') else 'No URL'}...")
    if article.get('summary'):
        print(f"   Summary: {article['summary'][:150]}...")
    if article.get('sentiment_score'):
        print(f"   Sentiment: {article['sentiment_score']:.2f}/100")

print("\n" + "="*60)
