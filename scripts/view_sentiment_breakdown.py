"""Display sentiment analysis breakdown for the latest articles"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_manager import DatabaseManager

db = DatabaseManager()

"""Display sentiment analysis breakdown for the latest articles"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_manager import DatabaseManager

db = DatabaseManager()

# First try to find articles with sentiment scores
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT date FROM articles 
    WHERE sentiment_score IS NOT NULL
    ORDER BY date DESC 
    LIMIT 1
""")
result = cursor.fetchone()

if result:
    # We have sentiment scores
    latest_date = str(result[0])
    has_sentiment = True
else:
    # No sentiment scores, use most recent date anyway
    cursor.execute("""
        SELECT date FROM articles 
        ORDER BY date DESC 
        LIMIT 1
    """)
    result = cursor.fetchone()
    if not result:
        print("No articles found in database.")
        cursor.close()
        conn.close()
        exit()
    latest_date = str(result[0])
    has_sentiment = False

if has_sentiment:
    # Get all articles from the latest date with sentiment scores
    cursor.execute("""
        SELECT article_type, sentiment_score, title, source, url
        FROM articles 
        WHERE date = %s AND sentiment_score IS NOT NULL
        ORDER BY article_type, sentiment_score DESC
    """, (latest_date,))
    articles = cursor.fetchall()
else:
    # Get all articles from the latest date (without sentiment scores)
    cursor.execute("""
        SELECT article_type, title, source, url
        FROM articles 
        WHERE date = %s
        ORDER BY article_type, title
    """, (latest_date,))
    articles = cursor.fetchall()

# Get daily data sentiment scores for comparison
cursor.execute("""
    SELECT sentiment_score, company_sentiment, macro_sentiment FROM daily_data 
    WHERE date = %s
""", (latest_date,))
daily_result = cursor.fetchone()
daily_sentiment = float(daily_result[0]) if daily_result and daily_result[0] else None
company_sentiment = float(daily_result[1]) if daily_result and daily_result[1] else None
macro_sentiment = float(daily_result[2]) if daily_result and daily_result[2] else None

cursor.close()
conn.close()

if not articles:
    print(f"No articles found for {latest_date}.")
    exit()

print("\n" + "="*80)
if has_sentiment:
    print(f"SENTIMENT ANALYSIS FOR {latest_date}")
else:
    print(f"ARTICLES FOR {latest_date} (No sentiment scores calculated yet)")
print("="*80)

if has_sentiment:
    # Separate articles by type with sentiment scores
    company_articles = [(score, title, source, url) for art_type, score, title, source, url in articles if art_type == 'company']
    macro_articles = [(score, title, source, url) for art_type, score, title, source, url in articles if art_type == 'macro']

    # Calculate averages
    company_avg = sum(score for score, _, _, _ in company_articles) / len(company_articles) if company_articles else 0
    macro_avg = sum(score for score, _, _, _ in macro_articles) / len(macro_articles) if macro_articles else 0

    print(f"\nCOMPANY ARTICLES SENTIMENT ({len(company_articles)} articles)")
    print(f"Average: {company_avg:.2f}")
    print("-" * 60)
    for i, (score, title, source, url) in enumerate(company_articles, 1):
        print(f"{i:2d}. [{score:6.2f}] {source}")
        print(f"    {title[:70]}{'...' if len(title) > 70 else ''}")
        print(f"    {url}")

    print(f"\nMACRO ARTICLES SENTIMENT ({len(macro_articles)} articles)")
    print(f"Average: {macro_avg:.2f}")
    print("-" * 60)
    for i, (score, title, source, url) in enumerate(macro_articles, 1):
        print(f"{i:2d}. [{score:6.2f}] {source}")
        print(f"    {title[:70]}{'...' if len(title) > 70 else ''}")
        print(f"    {url}")

    print(f"\n" + "="*80)
    print("SENTIMENT CALCULATION")
    print("="*80)
    print(f"Company sentiment average: {company_avg:.2f}")
    print(f"Macro sentiment average:   {macro_avg:.2f}")

    # Calculate 40/60 weighted average (40% company, 60% macro)
    if company_articles and macro_articles:
        weighted_sentiment = (company_avg * 0.4) + (macro_avg * 0.6)
        print(f"\nWeighted sentiment (40% company + 60% macro): {weighted_sentiment:.2f}")
        
        if daily_sentiment is not None:
            print(f"Daily data sentiment score: {daily_sentiment:.2f}")
            if abs(weighted_sentiment - daily_sentiment) < 0.01:
                print("✓ Calculation matches daily data")
            else:
                print(f"⚠ Difference: {abs(weighted_sentiment - daily_sentiment):.2f}")
    else:
        print("\n⚠ Cannot calculate weighted sentiment - missing article types")
else:
    # Show articles without sentiment scores
    company_articles = [(title, source, url) for art_type, title, source, url in articles if art_type == 'company']
    macro_articles = [(title, source, url) for art_type, title, source, url in articles if art_type == 'macro']

    print(f"\nCOMPANY ARTICLES ({len(company_articles)} articles)")
    print("-" * 60)
    for i, (title, source, url) in enumerate(company_articles, 1):
        print(f"{i:2d}. {source}")
        print(f"    {title[:70]}{'...' if len(title) > 70 else ''}")
        print(f"    {url}")

    print(f"\nMACRO ARTICLES ({len(macro_articles)} articles)")
    print("-" * 60)
    for i, (title, source, url) in enumerate(macro_articles, 1):
        print(f"{i:2d}. {source}")
        print(f"    {title[:70]}{'...' if len(title) > 70 else ''}")
        print(f"    {url}")

print(f"\n" + "="*80)
print("SENTIMENT CALCULATION")
print("="*80)

if company_sentiment is not None and macro_sentiment is not None:
    print("SAVED SENTIMENT SCORES:")
    print(f"Company sentiment: {company_sentiment:.2f}")
    print(f"Macro sentiment:   {macro_sentiment:.2f}")
    
    # Calculate 60/40 weighted average (60% company, 40% macro - matches sentiment agent)
    calculated_weighted = (company_sentiment * 0.6) + (macro_sentiment * 0.4)
    print(f"\nCalculated weighted (60% company + 40% macro): {calculated_weighted:.2f}")
    
    if daily_sentiment is not None:
        print(f"Stored daily sentiment score: {daily_sentiment:.2f}")
        if abs(calculated_weighted - daily_sentiment) < 0.01:
            print("✓ Calculation matches stored daily score")
        else:
            print(f"⚠ Difference: {abs(calculated_weighted - daily_sentiment):.2f}")
else:
    print("No sentiment scores calculated yet for this date.")
    print("Process: Articles → Individual scores → Company/Macro averages → Final 40/60 weighted score")
    
    if daily_sentiment is not None:
        print(f"\nCurrent daily sentiment score: {daily_sentiment:.2f}")

print(f"\n" + "="*80 + "\n")

print(f"\n" + "="*80 + "\n")