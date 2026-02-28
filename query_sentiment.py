"""Quick query: sentiment data from daily_data"""
from data.database_manager import DatabaseManager

db = DatabaseManager()
conn = db.get_connection()
cur = conn.cursor()

cur.execute("""
    SELECT date, sentiment_score, company_sentiment, macro_sentiment 
    FROM daily_data 
    ORDER BY date
""")
rows = cur.fetchall()

print()
header = f"{'DATE':12s} | {'SENTIMENT':>10s} | {'COMPANY':>10s} | {'MACRO':>10s}"
print(header)
print("-" * len(header))

for r in rows:
    date = str(r[0])
    sent = f"{float(r[1]):.2f}" if r[1] is not None else "None"
    comp = f"{float(r[2]):.2f}" if r[2] is not None else "None"
    macro = f"{float(r[3]):.2f}" if r[3] is not None else "None"
    print(f"{date:12s} | {sent:>10s} | {comp:>10s} | {macro:>10s}")

print(f"\nTotal rows: {len(rows)}")
cur.close()
conn.close()
