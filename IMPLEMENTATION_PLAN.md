i # NVIDIA Stock Prediction - Implementation Plan

## Project Overview
Multi-agent AI system using LangChain to predict NVIDIA stock movements by analyzing news sentiment and technical indicators.

## Tech Stack
- **Language**: Python 3.10+
- **AI Framework**: LangChain
- **LLM**: OpenAI GPT-4
- **Database**: PostgreSQL
- **APIs**: 
  - Serper API (news search)
  - OpenAI API (sentiment analysis & decision making)
  - Yahoo Finance API (stock data via yfinance)
- **Libraries**: pandas, yfinance, psycopg2, langchain, openai, requests, pandas-ta

## System Architecture

### AI Agents (Use GPT-4):
1. **News Agent** - Searches and filters relevant NVIDIA news articles
2. **Sentiment Agent** - Analyzes articles and generates sentiment scores
3. **Orchestrator Agent** - Coordinates all agents and handles workflow

### Tools/Utilities (No LLM):
- Market Data Fetcher (yfinance)
- Database Manager (PostgreSQL operations)
- Technical Indicator Calculator (RSI, MACD, Moving Averages)

### Future Addition:
- **Prediction Agent** - ML model (Random Forest/LSTM) after 100+ days of data

## Database Schema

### Table: daily_data
```sql
- id: SERIAL PRIMARY KEY
- date: DATE UNIQUE NOT NULL
- open_price: DECIMAL(10,2)
- close_price: DECIMAL(10,2)
- high_price: DECIMAL(10,2)
- low_price: DECIMAL(10,2)
- volume: BIGINT
- rsi: DECIMAL(5,2)
- macd: DECIMAL(10,4)
- macd_signal: DECIMAL(10,4)
- moving_avg_50: DECIMAL(10,2)
- moving_avg_200: DECIMAL(10,2)
- sentiment_score: DECIMAL(6,2)
- next_day_close: DECIMAL(10,2)
- price_change_percent: DECIMAL(6,2)
- prediction: DECIMAL(10,2)
- prediction_accuracy: DECIMAL(6,2)
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### Table: articles
```sql
- id: SERIAL PRIMARY KEY
- date: DATE NOT NULL
- url: TEXT
- source: VARCHAR(255)
- title: TEXT
- summary: TEXT
- sentiment_score: DECIMAL(6,2)
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

## Implementation Phases

### Phase 1: Setup & Infrastructure (Day 1)
**Goal**: Set up development environment and database

**Tasks**:
- [ ] Install PostgreSQL on Windows
- [ ] Create virtual environment
- [ ] Install Python dependencies
- [ ] Create `.env` file for API keys
- [ ] Run database setup script
- [ ] Verify database connection

**Deliverables**:
- Working PostgreSQL database
- Python environment with all libraries
- Database tables created

---

### Phase 2: Market Data Agent (Day 1-2)
**Goal**: Fetch and store NVIDIA stock data with technical indicators

**Tasks**:
- [ ] Create MarketDataFetcher utility class
- [ ] Implement Yahoo Finance data retrieval
- [ ] Calculate technical indicators (RSI, MACD, MAs)
- [ ] Create DatabaseManager utility
- [ ] Store market data in PostgreSQL
- [ ] Test with manual run

**Deliverables**:
- `utils/market_data_fetcher.py`
- `utils/database_manager.py`
- Working stock data pipeline

**Test Command**: `python test_market_data.py`

---

### Phase 3: News Search Agent (Day 2-3)
**Goal**: Build AI agent to search and filter relevant news

**Tasks**:
- [ ] Set up Serper API integration
- [ ] Create NewsAgent using LangChain
- [ ] Define trusted news sources list
- [ ] Implement article filtering logic (GPT-4 decides relevance)
- [ ] Get top 3 articles from last 24 hours
- [ ] Store article metadata in database
- [ ] Test with manual run

**Deliverables**:
- `agents/news_agent.py`
- `config/trusted_sources.py`
- Working news collection pipeline

**Test Command**: `python test_news_agent.py`

---

### Phase 4: Sentiment Analysis Agent (Day 3-4)
**Goal**: Build AI agent to analyze article sentiment

**Tasks**:
- [ ] Create SentimentAgent using LangChain
- [ ] Implement GPT-4 article summarization
- [ ] Implement sentiment scoring (-100 to +100)
- [ ] Combine multiple article scores
- [ ] Store sentiment data in database
- [ ] Test with sample articles

**Deliverables**:
- `agents/sentiment_agent.py`
- Working sentiment analysis pipeline

**Test Command**: `python test_sentiment_agent.py`

---

### Phase 5: Orchestrator & Automation (Day 4-5)
**Goal**: Coordinate all agents and automate daily execution

**Tasks**:
- [ ] Create OrchestratorAgent using LangChain
- [ ] Implement workflow coordination
- [ ] Add error handling and logging
- [ ] Create main.py entry point
- [ ] Set up Windows Task Scheduler
- [ ] Test end-to-end pipeline
- [ ] Monitor for 3-5 days

**Deliverables**:
- `agents/orchestrator_agent.py`
- `main.py`
- `logs/` directory with daily logs
- Automated daily execution

**Automation**: Task Scheduler runs daily at 4:30 PM ET

---

### Phase 6: Data Collection Period (Days 6-100)
**Goal**: Collect 100+ days of data for model training

**Tasks**:
- [ ] Monitor system daily (first week)
- [ ] Monitor system weekly (weeks 2-4)
- [ ] Fix any errors that arise
- [ ] Verify data quality periodically
- [ ] Wait for sufficient data accumulation

**Success Metrics**:
- 95%+ successful daily runs
- All data fields populated
- No major gaps in data

**Duration**: ~3-4 months

---

### Phase 7: Prediction Model (After 100+ days)
**Goal**: Build and deploy ML prediction model

**Tasks**:
- [ ] Data preprocessing and feature engineering
- [ ] Train Random Forest model
- [ ] Evaluate model performance
- [ ] Create PredictionAgent
- [ ] Integrate into daily pipeline
- [ ] Track prediction accuracy over time
- [ ] Iterate and improve model

**Deliverables**:
- `models/prediction_model.py`
- `agents/prediction_agent.py`
- Model performance metrics

**Test Command**: `python train_model.py`

---

### Phase 8: Enhancement & Visualization (Optional - Future)
**Goal**: Add web dashboard and API

**Tasks**:
- [ ] Build FastAPI backend
- [ ] Create Streamlit dashboard
- [ ] Visualize predictions vs actual
- [ ] Show sentiment trends
- [ ] Display model accuracy metrics

**Deliverables**:
- Web dashboard
- REST API endpoints

---

## Daily Workflow (Automated)

**Time**: 4:30 PM ET (after market close)

```
1. Orchestrator Agent starts
   ↓
2. Market Data Fetcher runs
   - Fetch NVIDIA stock data (NVDA)
   - Calculate technical indicators
   - Store in database
   ↓
3. News Agent runs
   - Search for NVIDIA news (last 24 hours)
   - Filter by trusted sources
   - Get top 3 most relevant articles
   - Store article metadata
   ↓
4. Sentiment Agent runs
   - Summarize each article
   - Score sentiment (-100 to +100)
   - Combine scores into daily sentiment
   - Store in database
   ↓
5. Prediction Agent runs (after 100 days)
   - Load historical data
   - Run ML model
   - Predict next day's movement
   - Store prediction
   ↓
6. Log results and exit
```

## Cost Estimate

### Monthly Costs:
- **Serper API**: $5 one-time credit (lasts months) → ~$0/month initially
- **OpenAI API**: 
  - ~3 articles/day × $0.01 per article = $0.03/day
  - Orchestrator + News Agent decisions = $0.05/day
  - **Total**: ~$2.50/month
- **PostgreSQL**: Free (local)
- **Yahoo Finance**: Free
- **Hosting**: Free (local) or $5-10/month (cloud - optional)

**Total Initial Cost**: ~$2.50-5/month ✅ (Well under $20 budget)

## Environment Variables Required

Create `.env` file:
```
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
DATABASE_URL=postgresql://user:password@localhost:5432/nvidia_prediction
TIMEZONE=America/New_York
```

## Success Criteria

### MVP (Phase 5 Complete):
- ✅ System runs automatically daily
- ✅ Collects stock data with technical indicators
- ✅ Finds and analyzes 3 news articles
- ✅ Stores all data in PostgreSQL
- ✅ Logs show successful execution

### Full Project (Phase 7 Complete):
- ✅ 100+ days of clean data
- ✅ Working prediction model
- ✅ Prediction accuracy tracked
- ✅ System runs without manual intervention

### CV-Ready:
- ✅ Well-documented code
- ✅ Clean GitHub repository
- ✅ README with architecture diagram
- ✅ Demonstrated prediction results
- ✅ Can explain multi-agent architecture in interview

## Risk Mitigation

1. **API Rate Limits**: 
   - Use free tier limits carefully
   - Add retry logic with exponential backoff

2. **Market Holidays**: 
   - Orchestrator checks if market is open
   - Skips weekends/holidays

3. **Data Quality**:
   - Validate data before storing
   - Alert on missing/invalid data

4. **Model Overfitting**:
   - Use train/test split
   - Track out-of-sample performance
   - Keep model simple initially

## Next Steps

1. Set up environment (Phase 1)
2. Build and test each component individually
3. Integrate all components
4. Let it run and collect data
5. Build prediction model
6. Showcase on CV/GitHub

---

**Project Start Date**: January 12, 2026  
**Expected MVP**: January 17, 2026  
**Expected Full System**: April-May 2026 (after data collection)
