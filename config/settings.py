"""
Configuration settings for NVIDIA Stock Prediction System
Loads environment variables and provides centralized access to all settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================
# PROJECT PATHS
# ============================================
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env file
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# ============================================
# DATABASE CONFIGURATION
# ============================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "nvidia_prediction"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ============================================
# API KEYS
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# ============================================
# STOCK CONFIGURATION
# ============================================
STOCK_SYMBOL = os.getenv("STOCK_SYMBOL", "NVDA")
STOCK_NAME = "NVIDIA Corporation"

# ============================================
# MARKET SCHEDULE (Eastern Time)
# ============================================
MARKET_CLOSE_TIME = "16:00"  # 4:00 PM ET
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

# ============================================
# NEWS SEARCH SETTINGS
# ============================================
MAX_NEWS_ARTICLES = 3  # Number of articles to analyze daily
NEWS_SEARCH_DAYS_BACK = 1  # Search news from last N days
NEWS_RELEVANCE_THRESHOLD = 0.7  # Minimum relevance score (0-1)

# ============================================
# GPT MODEL SETTINGS
# ============================================
GPT_MODEL = "gpt-4"
GPT_TEMPERATURE = 0.7  # 0 = deterministic, 1 = creative
GPT_MAX_TOKENS = 1000

# ============================================
# TECHNICAL INDICATORS SETTINGS
# ============================================
RSI_PERIOD = 14  # Standard RSI period
MACD_FAST = 12   # MACD fast period
MACD_SLOW = 26   # MACD slow period
MACD_SIGNAL = 9  # MACD signal period
MA_SHORT = 50    # Short-term moving average
MA_LONG = 200    # Long-term moving average

# ============================================
# SENTIMENT SCORING
# ============================================
SENTIMENT_SCALE = (-100, 100)  # Sentiment range from -100 (very negative) to +100 (very positive)

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "nvidia_prediction.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================
# PREDICTION MODEL SETTINGS (Phase 7)
# ============================================
MIN_TRAINING_DAYS = 100  # Minimum days of data before training model
TRAIN_TEST_SPLIT = 0.8   # 80% training, 20% testing

# ============================================
# VALIDATION
# ============================================
def validate_config():
    """Validate that required configuration values are set"""
    errors = []
    
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not set in .env file")
    
    if not SERPER_API_KEY:
        errors.append("SERPER_API_KEY not set in .env file")
    
    if not DB_CONFIG["password"]:
        errors.append("DB_PASSWORD not set in .env file")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


# ============================================
# CONFIGURATION INFO (for debugging)
# ============================================
def get_config_info():
    """Return configuration summary (safe for logging)"""
    return {
        "stock_symbol": STOCK_SYMBOL,
        "gpt_model": GPT_MODEL,
        "max_articles": MAX_NEWS_ARTICLES,
        "timezone": TIMEZONE,
        "log_level": LOG_LEVEL,
        "db_host": DB_CONFIG["host"],
        "db_name": DB_CONFIG["database"],
        "openai_key_set": bool(OPENAI_API_KEY),
        "serper_key_set": bool(SERPER_API_KEY),
    }
