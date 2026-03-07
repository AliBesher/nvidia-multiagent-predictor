-- ============================================================================
-- Database Schema for NVIDIA Stock Prediction System
-- Updated: February 17, 2026 (Synced with live database)
-- Includes: Market data, sentiment analysis, gravity system, ML predictions
-- ============================================================================

-- Drop tables if they exist (for clean setup)
DROP VIEW IF EXISTS gravity_performance CASCADE;
DROP VIEW IF EXISTS daily_summary CASCADE;
DROP VIEW IF EXISTS recent_predictions CASCADE;
DROP TABLE IF EXISTS articles CASCADE;
DROP TABLE IF EXISTS daily_data CASCADE;

-- ============================================================================
-- Table: daily_data
-- Stores daily stock prices, technical indicators, sentiment, and predictions
-- ============================================================================
CREATE TABLE daily_data (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,

    -- Stock Price Data
    open_price NUMERIC(10,2),            -- Daily opening price
    close_price NUMERIC(10,2),           -- Daily closing price
    high_price NUMERIC(10,2),            -- Daily high price
    low_price NUMERIC(10,2),             -- Daily low price
    volume BIGINT,                       -- Daily trading volume

    -- Technical Indicators
    rsi NUMERIC(5,2),                    -- Relative Strength Index (0-100)
    macd NUMERIC(10,4),                  -- MACD value
    macd_signal NUMERIC(10,4),           -- MACD signal line
    moving_avg_50 NUMERIC(10,2),         -- 50-day moving average
    moving_avg_200 NUMERIC(10,2),        -- 200-day moving average
    bollinger_upper NUMERIC(10,2),       -- Bollinger Band upper (20-period, 2 std)
    bollinger_lower NUMERIC(10,2),       -- Bollinger Band lower
    bollinger_width NUMERIC(6,2),        -- Bollinger Width % (volatility measure)
    bollinger_pctb NUMERIC(6,4),         -- Bollinger %B (0=lower, 1=upper band)
    atr NUMERIC(10,2),                   -- Average True Range (14-period)
    atr_percent NUMERIC(6,2),            -- ATR as % of price
    volume_ratio NUMERIC(6,2),           -- Volume / 20-day avg volume

    -- Sentiment Analysis (separated by type)
    sentiment_score NUMERIC(6,2),        -- Combined sentiment (weighted: 60% company + 40% macro)
    company_sentiment NUMERIC(6,2),      -- Sentiment from NVIDIA-specific news (-100 to +100)
    macro_sentiment NUMERIC(6,2),        -- Sentiment from macro/market news (-100 to +100)
    sentiment_range VARCHAR(50),         -- Descriptive range label for sentiment level

    -- Next Day Results (for opening gap prediction)
    next_day_close NUMERIC(10,2),        -- Actual next day closing price
    next_day_open NUMERIC(10,2),         -- Actual next day opening price for gap calculation
    price_change_percent NUMERIC(6,2),   -- Close-to-close %: (next_day_close - current_close) / current_close * 100
    opening_gap_percent NUMERIC(6,2),    -- Opening gap %: (next_day_open - current_close) / current_close * 100

    -- Gravity System (Informational Gravity Model)
    gravity_score NUMERIC(6,2),          -- Gravity score from hybrid analysis (truth confrontation)
    gravity_accuracy NUMERIC(6,2),       -- Accuracy of gravity prediction vs actual movement (0-100%)
    gravity_grade VARCHAR(2),            -- Letter grade for gravity accuracy (A+, A, B+, B, C+, C, D, F)

    -- ML Prediction
    prediction NUMERIC(10,2),            -- ML model prediction value (1.0 = UP, -1.0 = DOWN)
    prediction_accuracy NUMERIC(6,2),    -- Accuracy of prediction vs actual result
    opening_prediction NUMERIC(10,2),    -- ML opening prediction (1.0 = GAP UP, -1.0 = GAP DOWN)

    -- Information Theory
    entropy VARCHAR(20),                 -- Market entropy/uncertainty level

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for daily_data
CREATE INDEX idx_daily_data_date ON daily_data(date);
CREATE INDEX idx_daily_data_next_day_open ON daily_data(next_day_open);
CREATE INDEX idx_daily_data_gravity_grade ON daily_data(gravity_grade);

-- ============================================================================
-- Table: articles
-- Stores news articles used for sentiment analysis
-- NOTE: NO foreign key to daily_data — articles can exist for weekends/holidays
-- ============================================================================
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,

    -- Article Information
    url TEXT,                            -- Article URL (unique per date)
    source VARCHAR(255),                 -- News source (Bloomberg, Reuters, etc.)
    title TEXT,                          -- Article headline
    summary TEXT,                        -- Short snippet from search results
    full_content TEXT,                   -- Complete article content (up to 10,000 chars)

    -- Article Classification
    article_type VARCHAR(20) DEFAULT 'company',  -- 'company' (NVIDIA-specific) or 'macro' (market/economy)

    -- Sentiment Analysis
    sentiment_score NUMERIC(6,2),        -- Individual article sentiment (-100 to +100)

    -- Gravity System
    gravitational_mass NUMERIC,          -- Calculated gravitational mass for gravity model

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unique constraint: one URL per date (prevents duplicate articles)
CREATE UNIQUE INDEX unique_article_per_date ON articles(date, url);

-- Indexes for articles
CREATE INDEX idx_articles_date ON articles(date);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_type ON articles(article_type);
CREATE INDEX idx_articles_type_date ON articles(article_type, date);

-- ============================================================================
-- View: recent_predictions
-- Quick view of recent prediction results
-- ============================================================================
CREATE VIEW recent_predictions AS
SELECT
    date,
    close_price,
    prediction,
    next_day_close,
    prediction_accuracy,
    sentiment_score,
    CASE
        WHEN prediction_accuracy IS NOT NULL THEN 'Completed'
        WHEN prediction IS NOT NULL THEN 'Pending'
        ELSE 'No Prediction'
    END as status
FROM daily_data
WHERE prediction IS NOT NULL
ORDER BY date DESC
LIMIT 30;

-- ============================================================================
-- View: daily_summary
-- Full daily overview joining daily_data with article counts
-- ============================================================================
CREATE VIEW daily_summary AS
SELECT
    dd.date,
    dd.close_price,
    dd.volume,
    dd.rsi,
    dd.macd,
    dd.moving_avg_50,
    dd.moving_avg_200,
    dd.sentiment_score,
    dd.company_sentiment,
    dd.macro_sentiment,
    dd.gravity_score,
    dd.gravity_grade,
    COUNT(a.id) as total_articles,
    COUNT(CASE WHEN a.article_type = 'company' THEN 1 END) as company_articles,
    COUNT(CASE WHEN a.article_type = 'macro' THEN 1 END) as macro_articles,
    dd.next_day_close,
    dd.next_day_open,
    dd.price_change_percent,
    dd.opening_gap_percent,
    dd.prediction,
    dd.prediction_accuracy
FROM daily_data dd
LEFT JOIN articles a ON dd.date = a.date
GROUP BY dd.id, dd.date
ORDER BY dd.date DESC;

-- ============================================================================
-- View: gravity_performance
-- Aggregate gravity model accuracy by grade
-- ============================================================================
CREATE VIEW gravity_performance AS
SELECT
    gravity_grade,
    COUNT(*) as prediction_count,
    AVG(gravity_accuracy) as avg_accuracy,
    AVG(ABS(price_change_percent)) as avg_actual_movement,
    COUNT(CASE WHEN gravity_accuracy > 60 THEN 1 END) as successful_predictions
FROM daily_data
WHERE gravity_grade IS NOT NULL AND gravity_accuracy IS NOT NULL
GROUP BY gravity_grade
ORDER BY gravity_grade;

-- ============================================================================
-- Column Documentation
-- ============================================================================
COMMENT ON TABLE daily_data IS 'Daily stock data with gravity system, sentiment analysis, and ML predictions';
COMMENT ON TABLE articles IS 'News articles with type classification (company/macro) — no FK constraint to daily_data';

-- daily_data columns
COMMENT ON COLUMN daily_data.sentiment_score IS 'Combined sentiment (weighted: 60% company + 40% macro)';
COMMENT ON COLUMN daily_data.company_sentiment IS 'Sentiment from NVIDIA-specific news (-100 to +100)';
COMMENT ON COLUMN daily_data.macro_sentiment IS 'Sentiment from macro/market news (-100 to +100)';
COMMENT ON COLUMN daily_data.sentiment_range IS 'Descriptive label for sentiment level';
COMMENT ON COLUMN daily_data.next_day_open IS 'Actual next day opening price for gap calculation';
COMMENT ON COLUMN daily_data.price_change_percent IS 'Close-to-close %: (next_day_close - current_close) / current_close * 100';
COMMENT ON COLUMN daily_data.opening_gap_percent IS 'Opening gap %: (next_day_open - current_close) / current_close * 100';
COMMENT ON COLUMN daily_data.gravity_score IS 'Informational gravity score from hybrid analysis';
COMMENT ON COLUMN daily_data.gravity_accuracy IS 'Accuracy of gravity prediction vs actual movement (0-100%)';
COMMENT ON COLUMN daily_data.gravity_grade IS 'Letter grade for gravity accuracy (A+ through F)';
COMMENT ON COLUMN daily_data.prediction IS 'ML prediction value (1.0 = UP, -1.0 = DOWN)';
COMMENT ON COLUMN daily_data.entropy IS 'Market entropy/uncertainty level';

-- articles columns
COMMENT ON COLUMN articles.article_type IS 'company = NVIDIA-specific news, macro = market/economy-wide news';
COMMENT ON COLUMN articles.gravitational_mass IS 'Calculated gravitational mass for informational gravity model';
