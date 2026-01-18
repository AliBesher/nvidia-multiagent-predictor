"""Test macro news collection"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.news_agent import NewsAgent
from datetime import datetime

# Initialize news agent
news_agent = NewsAgent()

# Test date
test_date = datetime.now().strftime("%Y-%m-%d")

print("\n" + "="*80)
print(f"TESTING MACRO NEWS COLLECTION FOR {test_date}")
print("="*80)

# Test company news
print("\n1. Testing Company News (NVIDIA-specific):")
print("-" * 80)
company_articles = news_agent.search_news(date=test_date, max_results=3)
print(f"Found {len(company_articles)} company articles:")
for i, article in enumerate(company_articles, 1):
    print(f"\n  {i}. [{article['source']}] {article['title']}")
    print(f"     Type: {article.get('article_type', 'N/A')}")
    print(f"     URL: {article['url'][:80]}...")

# Test macro news
print("\n\n2. Testing Macro News (Market/Economy):")
print("-" * 80)
macro_articles = news_agent.search_macro_news(date=test_date, max_results=3)
print(f"Found {len(macro_articles)} macro articles:")
for i, article in enumerate(macro_articles, 1):
    print(f"\n  {i}. [{article['source']}] {article['title']}")
    print(f"     Type: {article.get('article_type', 'N/A')}")
    print(f"     URL: {article['url'][:80]}...")

print("\n" + "="*80)
print(f"TOTAL: {len(company_articles)} company + {len(macro_articles)} macro = {len(company_articles) + len(macro_articles)} articles")
print("="*80 + "\n")
