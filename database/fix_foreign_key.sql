-- Fix: Remove foreign key constraint from articles table
-- This allows articles to be saved for weekends/holidays without requiring daily_data row

-- Drop the foreign key constraint
ALTER TABLE articles DROP CONSTRAINT IF EXISTS articles_date_fkey;

-- Articles can now be saved for any date, independent of daily_data
-- This makes sense because weekend news can affect next trading day sentiment

COMMIT;
