-- Database Schema Migration for NVIDIA Prediction System
-- Adding support for "Tail and Head" logic with Informational Gravity

-- Add new columns to DAILY_DATA table for aggregated results
ALTER TABLE daily_data 
ADD COLUMN IF NOT EXISTS sentiment_range TEXT,
ADD COLUMN IF NOT EXISTS entropy VARCHAR(20);

-- Add new columns to ARTICLES table for individual article analysis
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS gravitational_mass NUMERIC;

-- Add comments for documentation
COMMENT ON COLUMN daily_data.sentiment_range IS 'Probability range for sentiment (Tail) - e.g., "-10 to +20"';
COMMENT ON COLUMN daily_data.entropy IS 'Information dispersion level: High/Medium/Low';
COMMENT ON COLUMN articles.gravitational_mass IS 'Informational mass weight (0-10) for Data Physics analysis';
COMMENT ON COLUMN articles.sentiment_score IS 'Field Vector (-100 to +100) for individual articles';

-- Verify the changes
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name IN ('daily_data', 'articles') 
AND column_name IN ('sentiment_range', 'entropy', 'gravitational_mass')
ORDER BY table_name, column_name;