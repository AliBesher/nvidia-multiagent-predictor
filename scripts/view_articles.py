"""Display full articles from database"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_manager import DatabaseManager

db = DatabaseManager()
articles = db.get_articles_for_date('2026-01-16')

print("\n" + "="*80)
print(f"ARTICLES COLLECTED ON 2026-01-16 ({len(articles)} total)")
print("="*80)

for i, article in enumerate(articles, 1):
    print(f"\n{'─'*80}")
    print(f"ARTICLE {i}")
    print(f"{'─'*80}")
    print(f"Source:    {article.get('source', 'Unknown')}")
    print(f"Title:     {article['title']}")
    print(f"URL:       {article['url']}")
    print(f"\nSummary:")
    print(f"{article.get('summary', 'No summary available')}")
    if article.get('sentiment_score'):
        print(f"\nSentiment: {article['sentiment_score']:.2f}/100")

print("\n" + "="*80 + "\n")
