# 📈 NVIDIA Stock Prediction System

An AI-powered stock prediction system that combines real-time market data, news sentiment analysis, and technical indicators to predict NVIDIA (NVDA) stock movements.

**Current Version:** v2.0 MVP - Macro Sentiment & Prediction Ready  
**Previous Version:** v1.0 MVP - Data Collection & Sentiment Analysis  
**Status:** Production-ready, actively collecting data, prediction model integrated

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Version](https://img.shields.io/badge/version-2.0%20MVP-blue.svg)

## 🌟 Features

### v2.0 MVP Features (New)
- **Dual Sentiment Analysis**: Separate company-specific and macro/market sentiment (60/40 weighting)
- **Macro News Collection**: Tracks NASDAQ, S&P 500, Fed policy, and market-wide news
- **Prediction Agent**: Random Forest ML model for UP/DOWN prediction
- **Smart Date Handling**: Always uses last available trading day from Yahoo Finance
- **Duplicate Protection**: Market data saved once, articles accumulate across runs
- **Separate Trusted Source Lists**: Different sources optimized for company vs macro news (see below)

### v1.0 MVP Features
- **Automated Daily Data Collection**: Fetches NVIDIA stock data from Yahoo Finance with 50+ technical indicators
- **AI-Powered Sentiment Analysis**: Uses GPT-4 to analyze news articles from trusted sources (Bloomberg, Reuters, WSJ, etc.)
- **Smart News Filtering**: 3-tier source ranking system prioritizes high-quality financial news
- **Weekend Handling**: Intelligently accumulates weekend news and updates sentiment for the last trading day
- **PostgreSQL Database**: Stores historical market data, articles, and sentiment scores for model training
- **Timezone-Aware**: Works globally - automatically uses US Eastern Time for market operations
- **Bootstrap Protection**: Handles edge cases like starting the project on weekends or holidays

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                        │
│            (Coordinates Daily Workflow)                     │
└──────┬──────────────┬──────────────┬───────────────┬────────┘
       │              │              │               │
┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐ ┌─────▼─────┐
│ News Agent  │ │ Sentiment │ │ Prediction  │ │  Market   │
│(Serper API) │ │   Agent   │ │   Agent     │ │   Data    │
│             │ │ (GPT-4)   │ │(Random For.)│ │  Fetcher  │
│ • Company   │ │           │ │             │ │(Yahoo Fin)│
│ • Macro     │ │ • Company │ │ • Train     │ │           │
│             │ │ • Macro   │ │ • Predict   │ │           │
└──────┬──────┘ └─────┬─────┘ └──────┬──────┘ └─────┬─────┘
       │              │              │               │
       └──────────────┴──────────────┴───────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Database Manager  │
                    │   (PostgreSQL)     │
                    │                    │
                    │ • daily_data       │
                    │ • articles         │
                    │ • predictions      │
                    └────────────────────┘
```

## 📊 Data Pipeline

**Daily Workflow (runs at midnight Israel time / 5 PM ET):**

1. **Market Data Collection** (STEP 1)
   - Gets last trading day from Yahoo Finance (always has data)
   - If data exists in DB → skip (no duplicates)
   - If new → fetches OHLCV, calculates RSI, MACD, Moving Averages

2. **News Collection** (STEP 2)
   - **Company News**: NVIDIA-specific articles (3 articles)
   - **Macro News**: Market-wide news (NASDAQ, S&P 500, Fed) (3 articles)
   - Strict filtering: Each type has its own trusted source list (see below)

3. **Sentiment Analysis** (STEP 3)
   - GPT-4 analyzes company articles → Company Sentiment
   - GPT-4 analyzes macro articles → Macro Sentiment
   - **Combined Score = 60% Company + 40% Macro**

4. **Database Storage** (STEP 4 & 5)
   - Saves articles with `article_type` (company/macro)
   - Updates `company_sentiment`, `macro_sentiment`, `sentiment_score`
   - Links all data to last trading day

5. **Prediction** (STEP 6)
   - Checks if enough data (minimum 10 days)
   - If yes → trains Random Forest model → predicts UP/DOWN
   - If no → shows "Need X more days"

## � Trusted News Sources

I use **separate trusted source lists** for company vs macro news because different sources excel at different types of coverage.

### Company News Sources (NVIDIA-specific)

| Tier | Type | Sources | Best For |
|------|------|---------|----------|
| **1** | Premium | Bloomberg, Reuters, WSJ, CNBC, Financial Times | Breaking earnings, major deals |
| **2A** | Financial | Seeking Alpha, Barron's, Motley Fool, IBD, TheStreet | Earnings deep-dive, debt analysis, valuations, analyst ratings |
| **2B** | Tech | TechCrunch, The Verge, Ars Technica, Tom's Hardware, AnandTech, Wired | GPU launches, AI chips, product reviews |
| **3** | General | Yahoo Finance, MarketWatch, CNET, ZDNet, VentureBeat, Benzinga | Basic coverage |

**Why separate financial + tech sources?**
- Seeking Alpha writes great earnings analysis but won't cover GPU launches
- Tom's Hardware benchmarks GPUs but won't analyze debt-to-equity ratios
- I need BOTH to understand NVIDIA fully

### Macro News Sources (Market-wide)

| Tier | Sources | Best For |
|------|---------|----------|
| **1** | Bloomberg, Reuters, WSJ, Financial Times, CNBC | Fed policy, interest rates |
| **2** | MarketWatch, Barron's, Forbes, Business Insider, The Economist | Market analysis, economic trends |
| **3** | BBC Business, CNN Business, Yahoo Finance, Investing.com | General market news |

**Why different from company sources?**
- Macro news needs economic/policy focus (The Economist)
- Company news needs tech focus (Tom's Hardware, TechCrunch)
- Some overlap (Bloomberg, Reuters are excellent for both)

## �🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- OpenAI API Key
- Serper API Key

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Nvidiapred
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL**
```bash
# Create database
createdb nvidia_prediction

# Run schema
psql -d nvidia_prediction -f database/schema.sql
```

5. **Configure environment**

Create `.env` file:
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nvidia_prediction
DB_USER=postgres
DB_PASSWORD=your_password

# API Keys
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...

# Configuration
STOCK_SYMBOL=NVDA
GPT_MODEL=gpt-4
```

### Usage

**Check configuration:**
```bash
python main.py --info
```

**Test run (no database writes):**
```bash
python main.py --dry-run
```

**Production run:**
```bash
python main.py
```

**Run for specific date:**
```bash
python main.py --date 2026-01-15
```

**View collected data:**
```bash
python scripts/view_data.py
python scripts/view_articles.py
```

**Run tests:**
```bash
# Functional tests
python tests/test_integration.py     # Full workflow test
python tests/test_next_day.py        # Next day close logic
python tests/test_bootstrap.py       # Bootstrap edge case
python tests/test_timezone.py        # Timezone validation

# Structure tests (no API keys needed)
python tests/test_news_agent_structure.py
python tests/test_sentiment_agent_structure.py
python tests/test_orchestrator_structure.py
```

## 📅 Scheduling

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task: "NVIDIA Prediction"
3. Trigger: Daily at 12:00 AM (midnight)
4. Action: Start a program
   - Program: `C:\Projects\Nvidiapred\.venv\Scripts\python.exe`
   - Arguments: `C:\Projects\Nvidiapred\main.py`
   - Start in: `C:\Projects\Nvidiapred`

### Linux/Mac (Cron)

```bash
# Run at 5:00 PM ET daily
0 17 * * * cd /path/to/Nvidiapred && .venv/bin/python main.py
```

## 📁 Project Structure

```
Nvidiapred/
├── agents/                 # AI agents
│   ├── base_agent.py      # Base class for all agents
│   ├── news_agent.py      # News collection (Serper) - company + macro
│   ├── sentiment_agent.py # Sentiment analysis (GPT-4) - dual scoring
│   ├── prediction_agent.py # ML predictions (Random Forest) [NEW v2.0]
│   └── orchestrator_agent.py # Workflow coordinator
├── models/                # ML models [NEW v2.0]
│   └── prediction_model.py # Random Forest classifier
├── config/                # Configuration
│   ├── settings.py        # Environment settings
│   └── trusted_sources.py # News source rankings
├── database/              # Database setup
│   ├── schema.sql         # PostgreSQL schema
│   ├── add_macro_sentiment.sql # v2.0 column additions
│   └── setup.py           # Database initialization
├── utils/                 # Utilities
│   ├── database_manager.py    # PostgreSQL CRUD
│   ├── market_data_fetcher.py # Yahoo Finance API
│   ├── workflow_manager.py    # Weekend/holiday logic
│   └── logger.py              # Logging setup
├── tests/                 # Test files
│   └── test_prediction.py # Prediction agent tests [NEW v2.0]
├── scripts/               # Helper scripts
│   ├── view_data.py       # View database data
│   └── view_articles.py   # View collected articles
├── logs/                  # Application logs
├── main.py               # Entry point
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## 🗄️ Database Schema

### `daily_data` table
Stores daily market data and sentiment:
- Stock prices (OHLC)
- Volume
- Technical indicators (RSI, MACD, MAs)
- `sentiment_score` - Combined sentiment (60% company + 40% macro)
- `company_sentiment` - Company-specific sentiment [NEW v2.0]
- `macro_sentiment` - Market-wide sentiment [NEW v2.0]
- `prediction` - Model prediction (UP/DOWN) [NEW v2.0]
- Next day results (for model training)

### `articles` table
Stores news articles:
- URL, source, title, summary
- Publication date
- Individual sentiment score
- `article_type` - 'company' or 'macro' [NEW v2.0]
- Links to `daily_data` via date

## 🔧 Configuration

### Trusted News Sources (3-tier ranking)

**Tier 1 (Most Trusted):**
Bloomberg, Reuters, Wall Street Journal, Financial Times

**Tier 2 (Trusted):**
CNBC, MarketWatch, Barron's, Forbes

**Tier 3 (Acceptable):**
Seeking Alpha, Yahoo Finance, The Motley Fool

### Technical Indicators

- **RSI**: 14-period Relative Strength Index
- **MACD**: 12/26/9 Moving Average Convergence Divergence
- **MA_50**: 50-day Simple Moving Average
- **MA_200**: 200-day Simple Moving Average

## 📈 Roadmap

### v1.0 MVP (Completed - Data Collection Phase)
- [x] Phase 1: Database setup
- [x] Phase 2: Market data fetching with technical indicators
- [x] Phase 3: Automated news collection
- [x] Phase 4: AI sentiment analysis (GPT-4)
- [x] Phase 5: Weekend/holiday handling
- [x] Phase 6: Production deployment

### v2.0 MVP (Current - Macro Sentiment & Prediction)
- [x] Phase 7: Macro/market sentiment analysis (NASDAQ correlation)
- [x] Phase 8: Dual sentiment scoring (company + macro)
- [x] Phase 9: Prediction Agent with Random Forest
- [x] Phase 10: Smart date handling (always uses last trading day)
- [ ] Phase 11: Collect 10+ days (prediction starts)
- [ ] Phase 12: Collect 100+ days (reliable predictions)

### v3.0 (Future - Full AI Multi-Agent System)
- [ ] Upgrade all agents to GPT-4 intelligence
- [ ] Add range prediction (Strong Up/Weak Up/Flat/Weak Down/Strong Down)
- [ ] Implement agent-to-agent communication
- [ ] Real-time prediction with live data
- [ ] Web dashboard with visualizations
- [ ] Percentage change prediction (after 1000+ days)

---

## 🔄 Version 1.0 → 2.0 Changelog

### What Changed

| Feature | v1.0 | v2.0 |
|---------|------|------|
| **Sentiment Types** | Single score | Company + Macro (separate) |
| **Sentiment Weighting** | 100% company | 60% company + 40% macro |
| **News Collection** | Company only | Company + Market-wide |
| **Macro Sources** | N/A | Bloomberg, Reuters, CNBC, WSJ only |
| **Prediction** | Not implemented | Random Forest (UP/DOWN) |
| **Date Handling** | Uses current date | Uses last trading day from Yahoo |
| **Duplicate Runs** | Could fail | Safe (market data skipped if exists) |

### New Database Columns
```sql
ALTER TABLE daily_data ADD COLUMN company_sentiment DECIMAL(6,2);
ALTER TABLE daily_data ADD COLUMN macro_sentiment DECIMAL(6,2);
ALTER TABLE articles ADD COLUMN article_type VARCHAR(20);
```

### Why Macro Sentiment?
NVIDIA stock strongly correlates with NASDAQ and overall market conditions. When the market drops, NVIDIA typically drops regardless of company news. The 60/40 weighting reflects that company-specific news has more impact, but market conditions matter too.

---

## 🤖 Prediction Model Details

### Why Random Forest?

| Model | Pros | Cons | Data Needed |
|-------|------|------|-------------|
| **Random Forest** ✅ | Works with small data, handles mixed features, no normalization needed | Less accurate than deep learning | ~100 days |
| Linear Regression | Simple, interpretable | Assumes linear relationships | ~50 days |
| Neural Network | Most accurate | Needs huge data, complex | 10,000+ days |
| XGBoost | Very accurate | Prone to overfitting with small data | ~500 days |

**I chose Random Forest because:**
1. Works with my limited data (~10-100 days)
2. Handles mixed feature types (sentiment, RSI, volume)
3. Provides feature importance (which factors matter most)
4. Easy to improve as I collect more data

### Feature Engineering

**Features (X):**
| Feature | Description | Range |
|---------|-------------|-------|
| `sentiment_score` | Combined sentiment | -100 to +100 |
| `company_sentiment` | Company-specific sentiment | -100 to +100 |
| `macro_sentiment` | Market-wide sentiment | -100 to +100 |
| `rsi` | Relative Strength Index | 0 to 100 |
| `macd` | MACD indicator | varies |
| `price_change_percent` | Today's price change | -10% to +10% |
| `volume_ratio` | Volume vs 20-day average | 0.5 to 3.0 |

**Target (y):**
| Value | Meaning |
|-------|---------|
| 1 | Price went UP (next_day_close > close_price) |
| 0 | Price went DOWN (next_day_close < close_price) |

### Data Preprocessing

**StandardScaler (Standardization):**
- Transforms features to mean=0, std=1
- Formula: `z = (x - mean) / std`
- Kept in code for future model flexibility

**Why NOT Normalization (Min-Max)?**
- Random Forest doesn't need it! (uses decision trees)
- Trees only ask "is value > X?" - scale doesn't matter
- But I keep StandardScaler for when I add other models (Neural Networks need it)

### Prediction Phases

| Data Amount | Phase | Prediction Quality |
|-------------|-------|-------------------|
| 0-9 days | Cannot predict | ❌ Not enough data |
| 10-30 days | Basic prediction | ⚠️ Low confidence |
| 30-100 days | Improving | 📊 Medium confidence |
| 100-500 days | Good predictions | ✅ Production ready |
| 500+ days | Range prediction | 🎯 Strong/Weak Up/Down |
| 1000+ days | % prediction | 💰 Percentage change |

---

## 💡 MVP vs Multi-Agent Comparison

| Feature | v1.0 MVP | v2.0 MVP (Current) | v3.0 Full (Future) |
|---------|----------|-------------------|-------------------|
| **Company Sentiment** | ✅ GPT-4 | ✅ GPT-4 | ✅ GPT-4 |
| **Macro Sentiment** | ❌ None | ✅ GPT-4 | ✅ GPT-4 |
| **News Selection** | Rule-based | Rule-based | GPT-4 Agent |
| **Predictions** | ❌ None | ✅ Random Forest | GPT-4 + Ensemble |
| **Prediction Type** | N/A | UP/DOWN | Range + % |
| **AI Agents** | 1 | 2 (Sentiment + Prediction) | 4+ |
| **Monthly Cost** | ~$1 | ~$1-2 | ~$5-10 |
| **Status** | ✅ Complete | ✅ Live | 🚧 Planned |

## 💰 API Costs

- **Serper**: FREE (2,500 searches/month) - ~30-90 used monthly
- **OpenAI GPT-4**: ~$0.50-$1.00/month
- **Total**: ~$1/month

## 📖 Example Output

When you run `python main.py`, you'll see:

```
============================================================
                NVIDIA STOCK PREDICTION SYSTEM
              Daily Workflow Results - 2025-01-17
============================================================

📈 MARKET DATA
   Symbol: NVDA
   Date: 2025-01-17
   Open: $135.55
   High: $138.20
   Low: $134.97
   Close: $137.71
   Volume: 277,024,928
   Change: +$2.83 (+2.10%)

📰 NEWS SENTIMENT
   Company Articles Analyzed: 3
   Company Sentiment Score: -4.7/100
   Macro Articles Analyzed: 3
   Macro Sentiment Score: 35.0/100
   Combined Sentiment: 11.1/100 (60% company + 40% macro)

🔮 PREDICTION
   Status: Cannot predict yet
   Reason: Not enough data (5/10 days)
   
   → Need 5 more trading days of data to begin predictions
============================================================
```

Once you have 10+ days of data:
```
🔮 PREDICTION
   Tomorrow's Prediction: UP ⬆️
   Model Confidence: Based on 15 days of data
   
   Top Factors:
   - sentiment_score: 0.35
   - rsi: 0.25
   - volume_ratio: 0.20
============================================================
```

## 🤝 Contributing

This is a personal project, but suggestions are welcome! Please open an issue to discuss major changes.

## 📝 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

**This system is for educational and research purposes only.**

- Not financial advice
- No guarantee of prediction accuracy
- Use at your own risk
- Always do your own research before investing

## 🙏 Acknowledgments

- **Yahoo Finance** - Market data
- **Serper** - News search API
- **OpenAI** - GPT-4 sentiment analysis
- **LangChain** - AI agent framework

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**⭐ If you find this project useful, please consider giving it a star!**
