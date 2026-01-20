"""Quick script to view all collected data in the database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
import os
from dotenv import load_dotenv

# Load environment
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    port=int(os.getenv("DB_PORT", "1998")),
    database="nvidia_prediction",
    user="postgres",
    password=os.getenv("DB_PASSWORD", "")
)
cursor = conn.cursor()

# Get all data
query = """
    SELECT date, close_price, company_sentiment, macro_sentiment, sentiment_score, next_day_close, price_change_percent 
    FROM daily_data 
    ORDER BY date DESC
"""
cursor.execute(query)
rows = cursor.fetchall()

print("\n" + "="*100)
print("ALL COLLECTED DATA")
print("="*100)
print(f"{'Date':<12} | {'Close':>8} | {'Company':>8} | {'Macro':>7} | {'Combined':>8} | {'Next Day':>10} | {'Change':>8}")
print("-"*100)

for row in rows:
    date, close, company_sent, macro_sent, sentiment, next_close, change = row
    next_str = f"${next_close:.2f}" if next_close is not None else "TBD"
    change_str = f"+{change:.2f}%" if change is not None and change > 0 else f"{change:.2f}%" if change is not None else "N/A"
    company_str = f"{company_sent:>8.1f}" if company_sent is not None else "N/A".rjust(8)
    macro_str = f"{macro_sent:>7.1f}" if macro_sent is not None else "N/A".rjust(7)
    sentiment_str = f"{sentiment:>8.1f}" if sentiment is not None else "N/A".rjust(8)
    print(f"{date} | ${close:>7.2f} | {company_str} | {macro_str} | {sentiment_str} | {next_str:>10} | {change_str:>8}")

print("-"*100)
print(f"Total rows: {len(rows)}")
print("="*100)

cursor.close()
conn.close()
