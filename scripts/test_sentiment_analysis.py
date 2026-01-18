"""Test sentiment analysis with company and macro articles"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.news_agent import NewsAgent
from agents.sentiment_agent import SentimentAgent
from datetime import datetime

# Initialize agents
news_agent = NewsAgent()
sentiment_agent = SentimentAgent()

# Test date
test_date = datetime.now().strftime("%Y-%m-%d")

print("\n" + "="*80)
print(f"TESTING SENTIMENT ANALYSIS WITH COMPANY + MACRO NEWS")
print("="*80)

# Collect articles
print("\nStep 1: Collecting Articles...")
print("-" * 80)
company_articles = news_agent.search_news(date=test_date, max_results=3)
macro_articles = news_agent.search_macro_news(date=test_date, max_results=3)

print(f"✓ Found {len(company_articles)} company articles")
print(f"✓ Found {len(macro_articles)} macro articles")

# Analyze sentiment separately
print("\nStep 2: Analyzing Sentiment...")
print("-" * 80)
result = sentiment_agent.analyze_articles_by_type(company_articles, macro_articles)

# Display results
print("\n" + "="*80)
print("SENTIMENT ANALYSIS RESULTS")
print("="*80)

print(f"\n📊 COMPANY SENTIMENT (NVIDIA-specific):")
print(f"   Score: {result['company_sentiment']:.2f}/100")
print(f"   Confidence: {result['company_confidence']}")
print(f"   Key Factors: {result['company_factors']}")

print(f"\n🌍 MACRO SENTIMENT (Market/Economy):")
print(f"   Score: {result['macro_sentiment']:.2f}/100")
print(f"   Confidence: {result['macro_confidence']}")
print(f"   Key Factors: {result['macro_factors']}")

print(f"\n🎯 COMBINED SENTIMENT (60% company + 40% macro):")
print(f"   Score: {result['combined_score']:.2f}/100")
print(f"   Confidence: {result['combined_confidence']}")

print(f"\n📈 Article Count:")
print(f"   Company: {result['article_count']['company']}")
print(f"   Macro: {result['article_count']['macro']}")

print("\n" + "="*80 + "\n")
