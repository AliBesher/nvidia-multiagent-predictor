# 📋 PROJECT CONTEXT & STATE DOCUMENT
## For Future AI Assistant Sessions

---

## 🎯 **PROJECT OVERVIEW**

**Project Name**: NVIDIA Informational Gravity Engine  
**Current Version**: 3.0.0  
**Type**: Multi-Agent AI System for Financial Market Prediction  
**Primary Target**: NVIDIA (NVDA) stock prediction using news sentiment + technical analysis  
**Core Innovation**: Dynamic weight adjustment between sentiment and technical analysis based on market regime  

---

## 🧠 **CORE THEORY: INFORMATIONAL GRAVITY**

### **Fundamental Concept**
- Markets respond to **"Gravitational Mass"** of news, not just sentiment
- **High-Mass News** (earnings, $10B+ deals, concrete data) = strong gravity
- **Low-Mass Noise** (speculation, opinions) = weak gravity
- **Head**: Point of maximum probability (predicted price)
- **Tail**: Distribution of uncertainty from conflicting signals

### **Mathematical Foundation**
```
Final_Gravity = (Info_Gravity × W_s) + (Technical_Score × W_t)
Where W_s + W_t = 1.0 and weights are DYNAMIC (not fixed)
```

---

## 🤖 **MULTI-AGENT ARCHITECTURE**

### **Agent Hierarchy & Roles**

1. **BaseAgent** - Foundation class for all agents
2. **SentimentAgent (The Skeptic)** 
   - **Evolution**: Basic sentiment → Skeptical Financial Analyst
   - **Key Feature**: Caps scores at ±10 range (prevents "Information Black Holes")
   - **Purpose**: Filters speculation from concrete financial data
   
3. **StrategyAgent (The CEO)** - **MOST IMPORTANT INNOVATION**
   - **Role**: System mastermind that analyzes market regime
   - **Function**: Sets dynamic weights for Sentiment vs Technical analysis
   - **Range**: 20%-80% for each component (prevents extremes)
   - **Rules**: High-Mass Rule, Noise Rule, Technical Friction Rule

4. **OrchestratorAgent (The Conductor)**
   - **Function**: Coordinates all agents and implements hybrid decision engine
   - **Contains**: calculate_hybrid_signal() with StrategyAgent integration

5. **NewsAgent** - Collects and processes financial news
6. **PredictionAgent** - Generates final market predictions

### **Dynamic Weight System (Core Innovation)**

| Rule | Trigger | Weight Adjustment | Reasoning |
|------|---------|------------------|-----------|
| **Noise Rule** | Low news volume (<2 articles) | Technical: ↑80% | Market structure dominates |
| **High-Mass Rule** | Earnings, major catalysts | Sentiment: ↑80% | Information overwhelms technicals |
| **Technical Friction Rule** | Extreme RSI (>70 or <30) | Balanced: 60/40 | Overbought/oversold friction |

---

## 🏗️ **CURRENT ARCHITECTURE (Post-Restructuring)**

### **Directory Structure**
```
📁 /agents/               # Multi-Agent AI System (CORE)
├── base_agent.py         # Foundation for all agents
├── sentiment_agent.py    # The Skeptical Analyst
├── strategy_agent.py     # The Strategic CEO (CRITICAL)
├── orchestrator_agent.py # System conductor with hybrid engine
├── news_agent.py         # News collection
└── prediction_agent.py   # Final predictions

📁 /data/                 # Data Management (moved from /utils)
├── database_manager.py   # PostgreSQL operations
└── market_data_fetcher.py# Market data collection

📁 /views/                # Professional Dashboards (enhanced from /scripts)
├── strategy_dashboard.py # StrategyAgent analytics
├── sequential_analysis.py# Production backtesting
└── *_viewer.py          # Data visualization

📁 /database/             # Consolidated Schema (cleaned)
├── schema.sql           # Modern unified schema (ALL migrations consolidated)
└── setup.py            # Automated database setup

📁 /utils/               # Supporting utilities
├── logger.py            # Logging system
├── timezone_manager.py  # Market timezone handling
├── workflow_manager.py  # Process coordination
└── fix_grade_f_sentiments.py # Maintenance script

📁 /tests/               # Comprehensive test suite
📁 /docs/                # Technical documentation
📁 /config/              # Settings and configuration
📁 /models/              # ML prediction models
```

---

## 📊 **DATABASE SCHEMA (Consolidated)**

### **Key Tables**
1. **daily_data** - Enhanced with:
   - `company_sentiment` & `macro_sentiment` (separated)
   - `next_day_open` (for gap prediction)
   - `gravity_score` & `gravity_accuracy` & `gravity_grade`
   - No longer has basic sentiment_score only

2. **articles** - Enhanced with:
   - `article_type` ('company' vs 'macro')
   - **NO foreign key constraints** (allows weekend articles)

### **Important**: All migration files were REMOVED and consolidated into single schema.sql

---

## 🔄 **RECENT MAJOR CHANGES (Last 48 Hours)**

### **Architectural Transformation**
1. **File Reorganization**: 
   - Moved utils/database_manager.py → data/database_manager.py
   - Moved utils/market_data_fetcher.py → data/market_data_fetcher.py
   - Moved scripts/*.py → views/ with professional naming
   - Removed 35+ temporary test files

2. **Database Consolidation**:
   - Merged 5 migration files into single schema.sql
   - Removed: fix_foreign_key.sql, add_macro_sentiment.sql, etc.
   - Single source of truth for database structure

3. **Code Cleanup**:
   - Removed sentiment_agent_backup.py (orphaned legacy)
   - Removed empty /core folder
   - Removed /scripts folder (consolidated to /views)
   - Updated ALL import statements across codebase

### **Strategic Evolution**
- **From**: Fixed 60/40 sentiment/technical weights
- **To**: Dynamic weights (20%-80% range) via StrategyAgent
- **From**: Basic sentiment analysis
- **To**: Multi-agent system with regime detection

---

## ⚙️ **TECHNICAL IMPLEMENTATION DETAILS**

### **Sentiment Analysis**
- **Range**: Realistic ±10 scale (no more inflated +82 scores)
- **Types**: Separated company vs macro sentiment
- **Agent**: Uses GPT-4 with "Skeptical Constraints"

### **Technical Analysis**
- **Indicators**: RSI(14), 3-day momentum, MA distance
- **Scale**: Normalized to ±10 to match sentiment
- **Role**: "Market Friction" that dampens/amplifies news gravity

### **Hybrid Engine**
- **Formula**: Final_Gravity = (Info_Gravity × W_s) + (Technical_Score × W_t)
- **Weights**: Set dynamically by StrategyAgent based on market regime
- **Boundary Rules**: Prevent extreme allocations (20%-80% limits)

---

## 🎯 **PRODUCTION STATUS**

### **What Works**
- ✅ All agents functional and integrated
- ✅ Dynamic weight system operational
- ✅ Database with modern consolidated schema
- ✅ Professional modular architecture
- ✅ Import statements updated after reorganization
- ✅ Strategy dashboard for regime analysis
- ✅ Sequential backtesting engine

### **Known Issues**
- ⚠️ Environment may need `pip install -r requirements.txt`
- ⚠️ Database credentials need setup in .env file
- ⚠️ OpenAI API key required for GPT-4 integration

### **Entry Points**
```bash
python main.py                    # Main daily workflow
python views/strategy_dashboard.py # StrategyAgent analysis
python views/sequential_analysis.py # Backtesting engine
python main.py --info            # System status check
```

---

## 🧪 **KEY FILES TO UNDERSTAND**

### **Critical Files (Touch with Care)**
1. `agents/strategy_agent.py` - **Core innovation**, dynamic weight logic
2. `agents/orchestrator_agent.py` - Main coordinator with calculate_hybrid_signal()
3. `agents/sentiment_agent.py` - Enhanced with realistic constraints
4. `database/schema.sql` - Consolidated modern schema
5. `main.py` - Production entry point

### **Recent Creation**
- `views/strategy_dashboard.py` - Professional StrategyAgent analytics
- `database/setup.py` - Automated database initialization

### **Safe to Modify**
- View files in `/views/` - Dashboard and analysis tools
- Test files in `/tests/` - Testing components
- Documentation in `/docs/` - Supporting materials

---

## 📈 **PERFORMANCE & VALIDATION**

### **Grading System**
- **Grade A**: 90-100% accuracy (perfect direction + magnitude)
- **Grade B**: 80-89% (correct direction, good magnitude)
- **Grade C-F**: Decreasing accuracy levels

### **Backtest Capabilities**
- Sequential day-by-day analysis
- Dynamic weight tracking over time
- Regime change detection validation
- Truth confrontation (prediction vs actual)

---

## 🎨 **CODING STANDARDS & PATTERNS**

### **Import Pattern After Reorganization**
```python
from data.database_manager import DatabaseManager
from data.market_data_fetcher import MarketDataFetcher
from agents.orchestrator_agent import OrchestratorAgent
from agents.strategy_agent import StrategyAgent
```

### **Agent Pattern**
All agents inherit from BaseAgent and follow consistent initialization patterns.

### **Database Pattern**
All database operations go through DatabaseManager with proper connection handling.

---

## 🚨 **CRITICAL KNOWLEDGE FOR FUTURE SESSIONS**

1. **StrategyAgent is the KEY INNOVATION** - Never remove or simplify this
2. **Dynamic weights (20%-80%) are core feature** - Don't revert to fixed weights
3. **Schema is consolidated** - Don't recreate migration files
4. **Import paths changed** - data.* and views.* are new patterns
5. **No more inflated sentiment scores** - ±10 is the realistic range
6. **Multi-agent architecture** - Each agent has specific specialized role

---

## 📋 **TODO / FUTURE ENHANCEMENTS**

### **Immediate (if needed)**
- Environment setup verification
- Database connection testing
- API key configuration validation

### **Future Roadmap**
- Multi-asset expansion (beyond NVIDIA)
- Real-time execution integration
- Deep learning enhanced gravity calculations

---

## 💡 **CONTEXT FOR AI ASSISTANT**

### **User's Working Style**
- Prefers architectural thinking and clean code
- Values consolidation over scattered files
- Appreciates professional-grade organization
- Focuses on eliminating technical debt

### **Project Philosophy**
- **Theory-driven**: Everything based on Informational Gravity concept
- **Multi-agent**: Specialized AI agents with specific roles
- **Dynamic**: Adapts to market conditions rather than static rules
- **Professional**: Enterprise-grade architecture and documentation

### **Recent Focus Areas**
- Cleaning up legacy code and migrations
- Professional architecture restructuring
- Dynamic weight system implementation
- Comprehensive documentation

---

**🔑 KEY INSIGHT**: This project evolved from simple sentiment analysis to a sophisticated multi-agent AI system. The StrategyAgent represents the breakthrough innovation that makes this system unique in quantitative finance.**