-- Migration: Add macro sentiment tracking
-- Date: 2026-01-17
-- Purpose: Separate company-specific and macro/market sentiment

-- Add article_type column to articles table
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS article_type VARCHAR(20) DEFAULT 'company';

-- Add comment for clarity
COMMENT ON COLUMN articles.article_type IS 'Type of article: company (NVIDIA-specific) or macro (market/economy-wide)';

-- Add separate sentiment columns to daily_data table
ALTER TABLE daily_data 
ADD COLUMN IF NOT EXISTS company_sentiment DECIMAL(6,2),
ADD COLUMN IF NOT EXISTS macro_sentiment DECIMAL(6,2);

-- Add comments
COMMENT ON COLUMN daily_data.company_sentiment IS 'Sentiment from NVIDIA-specific news (-100 to +100)';
COMMENT ON COLUMN daily_data.macro_sentiment IS 'Sentiment from macro/market news (-100 to +100)';
COMMENT ON COLUMN daily_data.sentiment_score IS 'Combined sentiment score (weighted: 60% company + 40% macro)';

-- Update existing articles to be 'company' type (all existing are NVIDIA-specific)
UPDATE articles SET article_type = 'company' WHERE article_type IS NULL;

-- Create index for article_type queries
CREATE INDEX IF NOT EXISTS idx_articles_type_date ON articles(article_type, date);

COMMIT;
