#!/usr/bin/env python3
"""
Quick Database Schema Update
Adds the missing company_sentiment and macro_sentiment columns to existing database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

def update_database_schema():
    """Add missing columns to existing daily_data table"""
    
    print("🔧 Updating database schema to match consolidated version...")
    
    try:
        db = DatabaseManager()
        
        # SQL to add missing columns
        schema_updates = [
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS company_sentiment DECIMAL(6,2);",
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS macro_sentiment DECIMAL(6,2);",
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS next_day_open DECIMAL(10,2);",
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS gravity_score DECIMAL(6,2);",
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS gravity_accuracy DECIMAL(5,2);",
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS gravity_grade CHAR(1);",
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS sentiment_range VARCHAR(50);",
            "ALTER TABLE daily_data ADD COLUMN IF NOT EXISTS entropy VARCHAR(20);",
            
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS article_type VARCHAR(20) DEFAULT 'company';",
            
            "CREATE INDEX IF NOT EXISTS idx_daily_data_next_day_open ON daily_data(next_day_open);",
            "CREATE INDEX IF NOT EXISTS idx_daily_data_gravity_grade ON daily_data(gravity_grade);",
            "CREATE INDEX IF NOT EXISTS idx_articles_type ON articles(article_type);",
            
            # Update comments
            "COMMENT ON COLUMN daily_data.company_sentiment IS 'Sentiment from NVIDIA-specific news (-10 to +10)';",
            "COMMENT ON COLUMN daily_data.macro_sentiment IS 'Sentiment from macro/market news (-10 to +10)';",
            "COMMENT ON COLUMN daily_data.sentiment_score IS 'Combined sentiment score (weighted: 60% company + 40% macro)';",
            "COMMENT ON COLUMN articles.article_type IS 'Type of article: company (NVIDIA-specific) or macro (market/economy-wide)';"
        ]
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                for sql in schema_updates:
                    try:
                        cursor.execute(sql)
                        print(f"✓ {sql}")
                    except Exception as e:
                        print(f"⚠️  {sql} - {e}")
                
                conn.commit()
        
        print("✅ Database schema updated successfully!")
        print("📊 New features available:")
        print("   • Separated company vs macro sentiment")
        print("   • Opening gap prediction support")
        print("   • Gravity accuracy system")
        print("   • Enhanced article classification")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema update failed: {e}")
        return False

if __name__ == "__main__":
    update_database_schema()