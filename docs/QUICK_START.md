# 🚀 QUICK START GUIDE

## ⚡ Get Running in 5 Minutes

### Step 1: Get API Keys (5 minutes)

**OpenAI:**
1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)

**Serper:**
1. Go to: https://serper.dev
2. Sign up (Google login works)
3. Copy API key from dashboard

### Step 2: Update .env File (1 minute)

Open `.env` in the project folder and update:

```env
OPENAI_API_KEY=sk-paste-your-key-here
SERPER_API_KEY=paste-your-key-here
```

Save and close.

### Step 3: Test It! (1 minute)

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Check configuration
python main.py --info

# Test run (no database writes)
python main.py --dry-run

# Real run!
python main.py
```

## ✅ Expected Output

```
============================================================
NVIDIA Stock Prediction System
============================================================

✓ Configuration valid
✓ Orchestrator ready

📊 STEP 1: Collecting Market Data
----------------------------------------------------------
✓ Fetched market data:
  Close: $186.77
  Volume: 86,445,572
  RSI: 51.2

📰 STEP 2: Collecting News Articles
----------------------------------------------------------
✓ Collected 3 articles:
  1. [Bloomberg] NVIDIA...
  2. [Reuters] NVIDIA...
  3. [CNBC] NVIDIA...

🎯 STEP 3: Analyzing Sentiment
----------------------------------------------------------
✓ Sentiment analysis complete:
  Overall Score: 42.50
  Confidence: High

✓ Workflow completed successfully
```

## 📅 Daily Schedule

**Recommended:** Run at **5:00 PM Eastern Time**

Why? Market closes at 4:00 PM ET, data available by 4:30 PM.

### Option 1: Manual (During Testing)
```powershell
# Every day at 5 PM
python main.py
```

### Option 2: Automated (Windows Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
   - **Name:** NVIDIA Prediction
   - **Trigger:** Daily at 5:00 PM
   - **Action:** Start a program
   - **Program:** `C:\Projects\Nvidiapred\.venv\Scripts\python.exe`
   - **Arguments:** `C:\Projects\Nvidiapred\main.py`
   - **Start in:** `C:\Projects\Nvidiapred`

## 🔍 Check Results

### View Today's Data
```powershell
python -c "from utils.database_manager import DatabaseManager; from datetime import datetime; db = DatabaseManager(); data = db.get_daily_data(datetime.now().strftime('%Y-%m-%d')); print(f'Close: ${data[\"close_price\"]}' if data else 'No data yet')"
```

### Check Database Count
```powershell
python -c "from utils.database_manager import DatabaseManager; db = DatabaseManager(); print(f'Total days collected: {db.get_data_count()}')"
```

### View Logs
```powershell
Get-Content logs\nvidia_prediction.log -Tail 20
```

## 🎯 What to Expect

### First 30 Days
- ✓ System collects daily data
- ✓ Database fills with stock prices + sentiment
- ✓ You see patterns emerging

### Days 30-100
- ✓ More data = better patterns
- ✓ Weekend accumulation working
- ✓ Complete sentiment history

### After 100 Days
- 🚀 Ready to build prediction model!
- 🚀 Train on historical data
- 🚀 Start making predictions

## 💡 Pro Tips

1. **Run on weekends too!** Weekend news matters.
2. **Check logs** if anything seems off
3. **Dry-run first** when testing: `python main.py --dry-run`
4. **Monitor costs** (but it's cheap: ~$1/month)
5. **Backup database** weekly: pgAdmin → Backup tool

## ⚠️ Common Issues

**"API key not set"**
→ Check `.env` file has both keys

**"No articles found"**
→ Normal on slow news days, system continues

**"Market was closed"**
→ Normal on weekends/holidays

**Database error**
→ Check PostgreSQL is running

## 📊 Useful Commands

```powershell
# Show configuration
python main.py --info

# Test without saving
python main.py --dry-run

# Run for specific date
python main.py --date 2026-01-15

# Check market status
python -c "from utils.market_data_fetcher import MarketDataFetcher; print('Open' if MarketDataFetcher().is_market_open() else 'Closed')"

# View latest logs
Get-Content logs\nvidia_prediction.log -Tail 50
```

## 🎉 You're All Set!

The system is:
- ✅ Built
- ✅ Tested
- ✅ Documented
- ✅ Ready to run

**Just add API keys and go!**

---

**Need help?** Check:
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete overview
- [README_COMPLETE.md](README_COMPLETE.md) - Full documentation
- Logs in `logs/` folder
