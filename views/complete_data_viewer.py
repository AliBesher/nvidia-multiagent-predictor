"""View complete data for all rows in the database with all columns."""
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

# Get all data with all columns
query = """
    SELECT * FROM daily_data ORDER BY date DESC
"""
cursor.execute(query)
rows = cursor.fetchall()

# Get column names
column_names = [desc[0] for desc in cursor.description]

print("\n" + "="*100)
print("COMPLETE DATABASE RECORDS - ALL FIELDS")
print("="*100)

for i, row in enumerate(rows, 1):
    print(f"\n{'='*100}")
    print(f"RECORD #{i} - {row[column_names.index('date')]}")
    print(f"{'='*100}")
    
    for col_name, value in zip(column_names, row):
        if col_name in ['id', 'created_at', 'updated_at']:
            print(f"  {col_name:<25}: {value}")
        elif col_name in ['open_price', 'close_price', 'high_price', 'low_price', 'next_day_close', 'prediction']:
            print(f"  {col_name:<25}: ${value:.2f}" if value is not None else f"  {col_name:<25}: None")
        elif col_name in ['volume']:
            print(f"  {col_name:<25}: {value:,}" if value is not None else f"  {col_name:<25}: None")
        elif col_name in ['rsi', 'macd', 'macd_signal', 'moving_avg_50', 'moving_avg_200', 'sentiment_score', 'price_change_percent', 'prediction_accuracy']:
            print(f"  {col_name:<25}: {value}" if value is not None else f"  {col_name:<25}: None")
        else:
            print(f"  {col_name:<25}: {value}")

print(f"\n{'='*100}")
print(f"Total Records: {len(rows)}")
print("="*100 + "\n")

cursor.close()
conn.close()
