"""Display full articles from database"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_manager import DatabaseManager

db = DatabaseManager()

# Get articles from the last few days instead of just one date
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT * FROM articles 
    ORDER BY date DESC, created_at DESC 
    LIMIT 50
""")
articles = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
cursor.close()
conn.close()

if not articles:
    print("No articles found.")
    exit()

# Group articles by date
from collections import defaultdict
articles_by_date = defaultdict(list)
for article in articles:
    articles_by_date[str(article['date'])].append(article)

print("\n" + "="*80)
print(f"RECENT ARTICLES ({len(articles)} total from {len(articles_by_date)} dates)")
print("="*80)

total_article_count = 1
for date in sorted(articles_by_date.keys(), reverse=True):
    date_articles = articles_by_date[date]
    company_count = sum(1 for a in date_articles if a.get('article_type') == 'company')
    macro_count = sum(1 for a in date_articles if a.get('article_type') == 'macro')
    
    print(f"\n{'='*80}")
    print(f"DATE: {date} ({len(date_articles)} articles)")
    print(f"Company articles: {company_count}, Macro articles: {macro_count}")
    print(f"{'='*80}")
    
    for article in date_articles:
        print(f"\n{'─'*80}")
        print(f"ARTICLE {total_article_count} ({article.get('article_type', 'Unknown').upper()})")
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
        total_article_count += 1
