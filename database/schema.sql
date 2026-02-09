-- Modern Database Schema for NVIDIA Stock Prediction System
-- Updated: February 9, 2026 (Consolidated from migrations)
-- Includes: Macro sentiment, opening gap support, gravity accuracy, and corrected foreign keys

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS articles CASCADE;
DROP TABLE IF EXISTS daily_data CASCADE;

-- ============================================
-- Table: daily_data
-- Stores daily stock prices, technical indicators, sentiment, and predictions
-- ============================================
CREATE TABLE daily_data (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    
    -- Stock Price Data
    open_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    volume BIGINT,
    
    -- Technical Indicators
    rsi DECIMAL(5,2),                    -- Relative Strength Index (0-100)
    macd DECIMAL(10,4),                  -- MACD value
    macd_signal DECIMAL(10,4),           -- MACD signal line
    moving_avg_50 DECIMAL(10,2),         -- 50-day moving average
    moving_avg_200 DECIMAL(10,2),        -- 200-day moving average
    
    -- Enhanced Sentiment Analysis (separated by type)
    sentiment_score DECIMAL(6,2),        -- Combined sentiment score (weighted: 60% company + 40% macro)
    company_sentiment DECIMAL(6,2),      -- Sentiment from NVIDIA-specific news (-100 to +100)
    macro_sentiment DECIMAL(6,2),        -- Sentiment from macro/market news (-100 to +100)
    
    -- Next Day Results (enhanced for opening gap prediction)
    next_day_close DECIMAL(10,2),        -- Actual next day closing price
    next_day_open DECIMAL(10,2),         -- Actual next day opening price for gap calculation
    price_change_percent DECIMAL(6,2),   -- Opening gap percentage: (next_day_open - current_close) / current_close * 100
    
    -- Gravity Accuracy System
    gravity_score DECIMAL(6,2),          -- Informational gravity score for truth confrontation
    gravity_accuracy DECIMAL(5,2),       -- Accuracy of gravity prediction vs actual movement
    gravity_grade CHAR(1),               -- Letter grade for gravity prediction (A-F)
    
    -- Predictions (ML model)
    prediction DECIMAL(10,2),            -- Predicted next day price
    prediction_accuracy DECIMAL(6,2),    -- Accuracy of prediction vs actual
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimized indexes
CREATE INDEX idx_daily_data_date ON daily_data(date);
CREATE INDEX idx_daily_data_next_day_open ON daily_data(next_day_open);
CREATE INDEX idx_daily_data_gravity_grade ON daily_data(gravity_grade);

-- ============================================
-- Table: articles
-- Stores news articles used for sentiment analysis (NO foreign key constraint)
-- ============================================
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    
    -- Article Information
    url TEXT,
    source VARCHAR(255),                 -- News source (Bloomberg, Reuters, etc.)
    title TEXT,
    summary TEXT,                        -- Short snippet from search results
    full_content TEXT,                   -- Complete article content (up to 10,000 chars)
    
    -- Article Classification
    article_type VARCHAR(20) DEFAULT 'company',  -- Type: 'company' (NVIDIA-specific) or 'macro' (market/economy-wide)
    
    -- Sentiment Analysis
    sentiment_score DECIMAL(6,2),        -- Individual article sentiment (-100 to +100)
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
    -- NOTE: NO foreign key constraint to allow weekend/holiday articles
    -- Articles can be saved for any date, independent of daily_data
);

-- Optimized indexes
CREATE INDEX idx_articles_date ON articles(date);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_type ON articles(article_type);

-- ============================================
-- Enhanced Views with Modern Features
-- ============================================

-- View: recent_predictions (enhanced with gravity system)
CREATE VIEW recent_predictions AS
SELECT 
    date,
    close_price,
    prediction,
    next_day_close,
    next_day_open,
    prediction_accuracy,
    sentiment_score,
    company_sentiment,
    macro_sentiment,
    gravity_score,
    gravity_accuracy,
    gravity_grade,
    price_change_percent as opening_gap_percent,
    CASE 
        WHEN prediction_accuracy IS NOT NULL THEN 'Completed'
        WHEN prediction IS NOT NULL THEN 'Pending'
        ELSE 'No Prediction'
    END as status
FROM daily_data
WHERE prediction IS NOT NULL OR gravity_score IS NOT NULL
ORDER BY date DESC
LIMIT 30;

-- View: daily_summary (enhanced with article types and gravity)
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
    dd.price_change_percent as opening_gap_percent,
    dd.prediction,
    dd.prediction_accuracy
FROM daily_data dd
LEFT JOIN articles a ON dd.date = a.date
GROUP BY dd.id, dd.date
ORDER BY dd.date DESC;

-- View: gravity_performance (new - tracks prediction accuracy)
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

-- ============================================
-- Modern Comments for Documentation
-- ============================================
COMMENT ON TABLE daily_data IS 'Enhanced daily stock data with gravity system, macro sentiment, and opening gap support';
COMMENT ON TABLE articles IS 'News articles with type classification (company/macro) and no foreign key constraints';

COMMENT ON COLUMN daily_data.sentiment_score IS 'Combined sentiment score (weighted: 60% company + 40% macro)';
COMMENT ON COLUMN daily_data.company_sentiment IS 'Sentiment from NVIDIA-specific news (-100 to +100)';
COMMENT ON COLUMN daily_data.macro_sentiment IS 'Sentiment from macro/market news (-100 to +100)';
COMMENT ON COLUMN daily_data.next_day_open IS 'Actual next day opening price for gap calculation';
COMMENT ON COLUMN daily_data.price_change_percent IS 'Opening gap percentage: (next_day_open - current_close) / current_close * 100';
COMMENT ON COLUMN daily_data.gravity_score IS 'Informational gravity score for truth confrontation system';
COMMENT ON COLUMN daily_data.gravity_accuracy IS 'Accuracy of gravity prediction vs actual market movement';
COMMENT ON COLUMN daily_data.gravity_grade IS 'Letter grade (A-F) for gravity prediction performance';

COMMENT ON COLUMN articles.article_type IS 'Type of article: company (NVIDIA-specific) or macro (market/economy-wide)';
