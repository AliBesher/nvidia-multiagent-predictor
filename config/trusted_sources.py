"""
Trusted news sources configuration
Separate lists for COMPANY news (NVIDIA-specific) and MACRO news (market-wide)
"""

# ============================================
# COMPANY NEWS SOURCES (NVIDIA-specific)
# Two types needed:
#   1. FINANCIAL: Earnings, revenue, debt, valuation, analyst ratings
#   2. TECH: Product launches, GPU reviews, AI developments
# ============================================

# Tier 1: Premium Financial & Tech (Most Reliable)
# These cover BOTH financial analysis AND tech news
COMPANY_TIER_1_SOURCES = [
    "Bloomberg",           # Excellent for earnings, valuation, AND tech
    "Reuters",             # Breaking news on earnings, deals
    "The Wall Street Journal",  # Deep financial analysis
    "CNBC",               # Earnings calls, analyst ratings
    "Financial Times",     # Company financials, valuations
]

# Tier 2A: Company Financial Analysis
# Best for: Earnings, revenue, debt, P/E ratio, analyst ratings
COMPANY_TIER_2_FINANCIAL = [
    "Seeking Alpha",       # Deep dive: earnings, DCF, valuation
    "Barron's",           # Stock analysis, price targets
    "Forbes",             # Company profiles, billionaire news
    "Business Insider",   # Company news, insider trading
    "Motley Fool",        # Stock analysis, earnings breakdown
    "Investor's Business Daily",  # Stock ratings, financials
    "TheStreet",          # Earnings, analyst upgrades/downgrades
]

# Tier 2B: Tech & Product News
# Best for: GPU launches, AI chips, product reviews, Jensen Huang
COMPANY_TIER_2_TECH = [
    "TechCrunch",         # AI/ML news, startup partnerships
    "The Verge",          # Product launches, tech industry
    "Ars Technica",       # Deep tech analysis
    "Tom's Hardware",     # GPU benchmarks, hardware news
    "AnandTech",          # Technical deep-dives
    "Wired",              # Tech industry, AI developments
]

# Tier 3: General coverage (still reliable)
COMPANY_TIER_3_SOURCES = [
    "Yahoo Finance",       # Earnings, basic financials
    "MarketWatch",        # Stock news, company updates
    "CNET",               # Product news
    "ZDNet",              # Enterprise tech
    "VentureBeat",        # AI/ML industry news
    "Benzinga",           # Stock movements, earnings
]

# Combined Tier 2 for company news
COMPANY_TIER_2_SOURCES = COMPANY_TIER_2_FINANCIAL + COMPANY_TIER_2_TECH

# ============================================
# MACRO NEWS SOURCES (Market-wide)
# Best for: Fed policy, interest rates, NASDAQ, S&P 500
# ============================================

# Tier 1: Premium Financial (Most Reliable for Macro News)
MACRO_TIER_1_SOURCES = [
    "Bloomberg",
    "Reuters",
    "The Wall Street Journal",
    "Financial Times",
    "CNBC",
]

# Tier 2: Financial & Market Focus
MACRO_TIER_2_SOURCES = [
    "MarketWatch",
    "Barron's",
    "Forbes",
    "Business Insider",
    "The Economist",
]

# Tier 3: General News with good business sections
MACRO_TIER_3_SOURCES = [
    "BBC Business",
    "CNN Business",
    "Yahoo Finance",
    "Investing.com",
]

# ============================================
# COMBINED LISTS (For backward compatibility)
# ============================================
COMPANY_TRUSTED_SOURCES = COMPANY_TIER_1_SOURCES + COMPANY_TIER_2_SOURCES + COMPANY_TIER_3_SOURCES
MACRO_TRUSTED_SOURCES = MACRO_TIER_1_SOURCES + MACRO_TIER_2_SOURCES + MACRO_TIER_3_SOURCES

# Legacy: All trusted sources (union of both)
TIER_1_SOURCES = list(set(COMPANY_TIER_1_SOURCES + MACRO_TIER_1_SOURCES))
TIER_2_SOURCES = list(set(COMPANY_TIER_2_SOURCES + MACRO_TIER_2_SOURCES))
TIER_3_SOURCES = list(set(COMPANY_TIER_3_SOURCES + MACRO_TIER_3_SOURCES))
TRUSTED_SOURCES = list(set(COMPANY_TRUSTED_SOURCES + MACRO_TRUSTED_SOURCES))

# ============================================
# EXCLUDED SOURCES (Unreliable/Low Quality)
# ============================================
EXCLUDED_SOURCES = [
    "reddit",
    "twitter",
    "facebook",
    "stocktwits",
    "4chan",
    "youtube comments",
]

# ============================================
# NVIDIA-SPECIFIC KEYWORDS (For Relevance Filtering)
# ============================================
NVIDIA_KEYWORDS = [
    "NVIDIA",
    "NVDA",
    "Jensen Huang",  # NVIDIA CEO
    "GeForce",
    "RTX",
    "CUDA",
    "AI chips",
    "GPU",
    "data center",
    "gaming graphics",
    "automotive",
    "Mellanox",
]

# Keywords that indicate market-moving news
HIGH_IMPACT_KEYWORDS = [
    "earnings",
    "revenue",
    "profit",
    "guidance",
    "forecast",
    "acquisition",
    "merger",
    "partnership",
    "lawsuit",
    "regulation",
    "stock split",
    "dividend",
    "analyst upgrade",
    "analyst downgrade",
    "price target",
]

# ============================================
# HELPER FUNCTIONS
# ============================================
def is_trusted_source(source_name: str) -> bool:
    """Check if a source is in ANY trusted list (legacy)"""
    return any(trusted.lower() in source_name.lower() for trusted in TRUSTED_SOURCES)


def is_trusted_company_source(source_name: str) -> bool:
    """Check if a source is trusted for COMPANY news (NVIDIA-specific)"""
    return any(trusted.lower() in source_name.lower() for trusted in COMPANY_TRUSTED_SOURCES)


def is_trusted_macro_source(source_name: str) -> bool:
    """Check if a source is trusted for MACRO news (market-wide)"""
    return any(trusted.lower() in source_name.lower() for trusted in MACRO_TRUSTED_SOURCES)


def is_excluded_source(source_name: str) -> bool:
    """Check if a source should be excluded"""
    return any(excluded.lower() in source_name.lower() for excluded in EXCLUDED_SOURCES)


def get_source_tier(source_name: str) -> int:
    """Get the tier level of a source (1 = best, 3 = acceptable, 0 = not trusted)"""
    if any(s.lower() in source_name.lower() for s in TIER_1_SOURCES):
        return 1
    elif any(s.lower() in source_name.lower() for s in TIER_2_SOURCES):
        return 2
    elif any(s.lower() in source_name.lower() for s in TIER_3_SOURCES):
        return 3
    return 0  # Not trusted


def get_company_source_tier(source_name: str) -> int:
    """Get tier for COMPANY news sources"""
    if any(s.lower() in source_name.lower() for s in COMPANY_TIER_1_SOURCES):
        return 1
    elif any(s.lower() in source_name.lower() for s in COMPANY_TIER_2_SOURCES):
        return 2
    elif any(s.lower() in source_name.lower() for s in COMPANY_TIER_3_SOURCES):
        return 3
    return 0  # Not trusted for company news


def get_macro_source_tier(source_name: str) -> int:
    """Get tier for MACRO news sources"""
    if any(s.lower() in source_name.lower() for s in MACRO_TIER_1_SOURCES):
        return 1
    elif any(s.lower() in source_name.lower() for s in MACRO_TIER_2_SOURCES):
        return 2
    elif any(s.lower() in source_name.lower() for s in MACRO_TIER_3_SOURCES):
        return 3
    return 0  # Not trusted for macro news
