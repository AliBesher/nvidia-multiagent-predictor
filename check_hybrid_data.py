#!/usr/bin/env python3

from utils.database_manager import DatabaseManager

def check_hybrid_data():
    """Check for hybrid prediction data in database"""
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
                print("Hybrid prediction data found:")
                for row in rows:
                    print(f"  {row[0]}: score={row[1]}, accuracy={row[2]}, grade={row[3]}")
            else:
                print("No hybrid prediction data found in date range")
                
                # Check if any gravity data exists
                cursor.execute("SELECT COUNT(*) FROM daily_data WHERE gravity_score IS NOT NULL")
                count = cursor.fetchone()[0]
                print(f"Total rows with gravity_score: {count}")
                
                # Show sample data structure
                cursor.execute("SELECT * FROM daily_data LIMIT 1")
                if cursor.fetchone():
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'daily_data' ORDER BY ordinal_position")
                    columns = [row[0] for row in cursor.fetchall()]
                    print(f"Available columns: {', '.join(columns)}")

if __name__ == "__main__":
    check_hybrid_data()