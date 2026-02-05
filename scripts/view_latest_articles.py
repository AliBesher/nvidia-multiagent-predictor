"""Display articles from the most recent day only"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_manager import DatabaseManager

db = DatabaseManager()

# Get the most recent date that has articles
conn = db.get_connection()
cursor = conn.cursor()
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

# Get all articles from the latest date
cursor.execute("""
    SELECT * FROM articles 
    WHERE date = %s
    ORDER BY created_at DESC
""", (latest_date,))
articles = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
cursor.close()
conn.close()

print("\n" + "="*80)
print(f"LATEST ARTICLES FROM {latest_date} ({len(articles)} total)")
print("="*80)

# Count article types
company_count = sum(1 for a in articles if a.get('article_type') == 'company')
macro_count = sum(1 for a in articles if a.get('article_type') == 'macro')
print(f"Company articles: {company_count}")
print(f"Macro articles: {macro_count}")
print("="*80)

for i, article in enumerate(articles, 1):
    print(f"\n{'─'*80}")
    print(f"ARTICLE {i} ({article.get('article_type', 'Unknown').upper()})")
    print(f"{'─'*80}")
    print(f"Date:      {article.get('date', 'Unknown')}")
    print(f"Type:      {article.get('article_type', 'Unknown').title()}")
    print(f"Source:    {article.get('source', 'Unknown')}")
    print(f"Title:     {article['title']}")
    print(f"URL:       {article['url']}")
    print(f"\nSummary:")
    print(f"{article.get('summary', 'No summary available')}")
    if article.get('sentiment_score'):
        print(f"\nSentiment: {article['sentiment_score']:.2f}/100")

print("\n" + "="*80 + "\n")