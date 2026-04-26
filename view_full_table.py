"""Quick script to display all daily_data in a formatted table"""
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute('''
    SELECT 
        date,
        close_price,
        company_sentiment,
        macro_sentiment,
        sentiment_score,
        prediction,
        opening_prediction,
        next_day_open,
        next_day_close,
        price_change_percent,
        opening_gap_percent,
        gravity_score,
        gravity_grade
    FROM daily_data
    ORDER BY date ASC
''')

rows = cur.fetchall()

# Header
hdr = (f"{'Date':<13} {'Close':>8} {'Company':>9} {'Macro':>8} {'Combined':>9} "
       f"{'Pred':>6} {'OpenPred':>9} {'NextOpen':>9} {'NextClose':>10} "
       f"{'Chg%':>7} {'Gap%':>7} {'Gravity':>8} {'Grade':>6}")
print(hdr)
print("-" * len(hdr))

for r in rows:
    date = str(r['date'])
    close = f"{r['close_price']:.2f}" if r['close_price'] else "   -"
    comp = f"{r['company_sentiment']:.1f}" if r['company_sentiment'] is not None else "   -"
    macro = f"{r['macro_sentiment']:.1f}" if r['macro_sentiment'] is not None else "   -"
    combined = f"{r['sentiment_score']:.1f}" if r['sentiment_score'] is not None else "   -"
    pred = f"{r['prediction']:.1f}" if r['prediction'] is not None else "  -"
    opred = f"{r['opening_prediction']:.1f}" if r['opening_prediction'] is not None else "   -"
    nopen = f"{r['next_day_open']:.2f}" if r['next_day_open'] is not None else "    -"
    nclose = f"{r['next_day_close']:.2f}" if r['next_day_close'] is not None else "     -"
    chg = f"{r['price_change_percent']:.2f}" if r['price_change_percent'] is not None else "   -"
    gap = f"{r['opening_gap_percent']:.2f}" if r['opening_gap_percent'] is not None else "   -"
    grav = f"{r['gravity_score']:.1f}" if r['gravity_score'] is not None else "   -"
    grade = r['gravity_grade'] if r['gravity_grade'] else "  -"

    print(f"{date:<13} {close:>8} {comp:>9} {macro:>8} {combined:>9} "
          f"{pred:>6} {opred:>9} {nopen:>9} {nclose:>10} "
          f"{chg:>7} {gap:>7} {grav:>8} {grade:>6}")

print(f"\nTotal rows: {len(rows)}")
conn.close()
