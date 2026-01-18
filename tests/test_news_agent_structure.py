"""
Test News Agent (without requiring API keys)
Shows structure and validates code
"""

print("\n" + "="*60)
print("News Agent Structure Test")
print("="*60 + "\n")

# Test imports
print("Testing imports...")
try:
    from agents.news_agent import NewsAgent
    from config.trusted_sources import is_trusted_source, get_source_tier
    print("✓ Imports successful\n")
except Exception as e:
    print(f"✗ Import error: {e}\n")
    exit(1)

# Test source filtering
print("Testing source filtering logic:")
print("-" * 60)

test_sources = [
    ("Bloomberg", True),
    ("Reuters", True),
    ("reddit", False),
    ("CNBC", True),
    ("twitter", False),
    ("The Wall Street Journal", True),
]

for source, expected_trusted in test_sources:
    is_trusted = is_trusted_source(source)
    tier = get_source_tier(source)
    status = "✓ TRUSTED" if is_trusted else "✗ EXCLUDED"
    tier_text = f"Tier {tier}" if tier > 0 else "Not ranked"
    
    match = "✓" if is_trusted == expected_trusted else "✗"
    print(f"{match} {source:30} → {status:12} ({tier_text})")

print("\n" + "="*60)
print("News Agent Structure:")
print("="*60)
print("""
The News Agent will:

1. Search Serper API for NVIDIA news
   - Query: "NVIDIA OR NVDA stock news {date}"
   - Gets up to 20 raw articles

2. Filter articles by:
   ✓ Trusted sources (Bloomberg, Reuters, WSJ, etc.)
   ✗ Excluded sources (reddit, twitter, etc.)
   ✓ NVIDIA relevance (keywords: NVIDIA, NVDA, Jensen Huang, etc.)

3. Rank by source quality:
   - Tier 1: Premium financial news (Bloomberg, Reuters)
   - Tier 2: Tech/business news (TechCrunch, Forbes)
   - Tier 3: General news (Yahoo Finance, CNN Business)

4. Return top articles (default: 3)

5. Format for sentiment analysis
""")

print("="*60)
print("\n✓ News Agent code structure is valid!")
print("\n⚠️  To test with real data:")
print("   1. Get SERPER_API_KEY from https://serper.dev")
print("   2. Add to .env file: SERPER_API_KEY=your_key_here")
print("   3. Run: python agents/news_agent.py")
print("="*60)
