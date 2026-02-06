-- Add gravity_accuracy column to daily_data table
-- Migration for Informational Gravity model accuracy tracking
-- Date: February 6, 2026

-- Add gravity_accuracy column first
ALTER TABLE daily_data 
ADD COLUMN IF NOT EXISTS gravity_accuracy NUMERIC(6,2);

-- Add comment for documentation
COMMENT ON COLUMN daily_data.gravity_accuracy IS 'Accuracy of Informational Gravity model prediction vs actual price movement (0-100%)';

-- Drop existing views before recreating them
DROP VIEW IF EXISTS recent_predictions CASCADE;
DROP VIEW IF EXISTS daily_summary CASCADE;

-- Recreate recent_predictions view with gravity accuracy
CREATE VIEW recent_predictions AS
SELECT 
    date,
    close_price,
    sentiment_score as predicted_score,
    next_day_close,
    price_change_percent,
    gravity_accuracy,
    CASE 
        WHEN gravity_accuracy IS NOT NULL THEN 'Accuracy Calculated'
        WHEN price_change_percent IS NOT NULL THEN 'Awaiting Accuracy'
        WHEN sentiment_score IS NOT NULL THEN 'Prediction Made'
        ELSE 'No Prediction'
    END as status
FROM daily_data
WHERE sentiment_score IS NOT NULL
ORDER BY date DESC
LIMIT 30;

-- Recreate daily_summary view with gravity accuracy
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
    dd.gravity_accuracy,
    dd.prediction,
    dd.prediction_accuracy
FROM daily_data dd
LEFT JOIN articles a ON dd.date = a.date
GROUP BY dd.id, dd.date
ORDER BY dd.date DESC;