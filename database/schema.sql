-- Database schema for NVIDIA stock prediction system
-- Created: January 12, 2026

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
    
    -- Sentiment Analysis
    sentiment_score DECIMAL(6,2),        -- Combined sentiment score (-100 to +100)
    
    -- Next Day Results (filled next day)
    next_day_close DECIMAL(10,2),        -- Actual next day closing price
    price_change_percent DECIMAL(6,2),   -- Percentage change to next day
    
    -- Predictions (Phase 7 - after model is trained)
    prediction DECIMAL(10,2),            -- Predicted next day price
    prediction_accuracy DECIMAL(6,2),    -- Accuracy of prediction vs actual
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on date for faster queries
CREATE INDEX idx_daily_data_date ON daily_data(date);

-- ============================================
-- Table: articles
-- Stores news articles used for sentiment analysis
-- ============================================
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    
    -- Article Information
    url TEXT,
    source VARCHAR(255),                 -- News source (Bloomberg, Reuters, etc.)
    title TEXT,
    summary TEXT,                        -- GPT-generated summary
    
    -- Sentiment Analysis
    sentiment_score DECIMAL(6,2),        -- Individual article sentiment (-100 to +100)
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to daily_data
    FOREIGN KEY (date) REFERENCES daily_data(date) ON DELETE CASCADE
);

-- Index on date for faster queries
CREATE INDEX idx_articles_date ON articles(date);
CREATE INDEX idx_articles_source ON articles(source);

-- ============================================
-- View: recent_predictions
-- Shows recent predictions with accuracy
-- ============================================
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

-- ============================================
-- View: daily_summary
-- Complete daily summary with all data
-- ============================================
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
    COUNT(a.id) as article_count,
    dd.next_day_close,
    dd.price_change_percent,
    dd.prediction,
    dd.prediction_accuracy
FROM daily_data dd
LEFT JOIN articles a ON dd.date = a.date
GROUP BY dd.id, dd.date
ORDER BY dd.date DESC;

-- ============================================
-- Comments for documentation
-- ============================================
COMMENT ON TABLE daily_data IS 'Daily stock data, technical indicators, sentiment scores, and predictions for NVIDIA stock';
COMMENT ON TABLE articles IS 'News articles collected and analyzed for sentiment';
COMMENT ON COLUMN daily_data.sentiment_score IS 'Combined sentiment score from all articles for this date (-100 to +100)';
COMMENT ON COLUMN daily_data.next_day_close IS 'Actual closing price of next trading day (filled next day)';
COMMENT ON COLUMN daily_data.price_change_percent IS 'Percentage change from today to next trading day';
COMMENT ON COLUMN daily_data.prediction IS 'ML model predicted next day closing price';
COMMENT ON COLUMN daily_data.prediction_accuracy IS 'Accuracy metric of prediction vs actual result';
