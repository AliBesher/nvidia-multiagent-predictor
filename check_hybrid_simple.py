#!/usr/bin/env python3
"""Check for hybrid prediction data"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger()

def check_hybrid_data():
    """Check for hybrid prediction data in database"""
    try:
        db = DatabaseManager()
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check specific date range
                cursor.execute("""
                    SELECT date, gravity_score, gravity_accuracy, gravity_grade 
                    FROM daily_data 
                    WHERE date BETWEEN %s AND %s 
                    ORDER BY date
                """, ('2026-02-08', '2026-02-11'))
                
                rows = cursor.fetchall()
                if rows:
                    print("✅ Hybrid prediction data found:")
                    for row in rows:
                        print(f"  📅 {row[0]}: score={row[1]}, accuracy={row[2]}, grade={row[3]}")
                else:
                    print("❌ No hybrid prediction data found in date range")
                    
                    # Check if any gravity data exists
                    cursor.execute("SELECT COUNT(*) FROM daily_data WHERE gravity_score IS NOT NULL")
                    count = cursor.fetchone()[0]
                    print(f"📊 Total rows with gravity_score: {count}")
                    
                    if count == 0:
                        print("\n🔍 Checking recent data for any gravity columns...")
                        cursor.execute("""
                            SELECT date, gravity_score, gravity_accuracy, gravity_grade 
                            FROM daily_data 
                            WHERE gravity_score IS NOT NULL 
                            ORDER BY date DESC 
                            LIMIT 5
                        """)
                        recent = cursor.fetchall()
                        if recent:
                            print("Recent hybrid data:")
                            for row in recent:
                                print(f"  📅 {row[0]}: score={row[1]}, accuracy={row[2]}, grade={row[3]}")
                        else:
                            print("No gravity data found in entire table")
                            
                        # Check sample data
                        cursor.execute("SELECT date FROM daily_data ORDER BY date DESC LIMIT 5")
                        dates = cursor.fetchall()
                        print("\n📅 Recent dates in daily_data:")
                        for date in dates:
                            print(f"  {date[0]}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_hybrid_data()