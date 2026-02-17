#!/usr/bin/env python3
"""Check database schema"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database_manager import DatabaseManager

def check_schema():
    db = DatabaseManager()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check daily_data columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'daily_data' 
            ORDER BY column_name
        """)
        daily_data_columns = cursor.fetchall()
        
        # Check articles columns  
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'articles' 
            ORDER BY column_name
        """)
        articles_columns = cursor.fetchall()
        
        # Check available tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print("DAILY_DATA COLUMNS:")
        for col in daily_data_columns:
            print(f"  {col[0]} ({col[1]})")
            
        print("\nARTICLES COLUMNS:")
        for col in articles_columns:
            print(f"  {col[0]} ({col[1]})")
            
        print("\nAVAILABLE TABLES:")
        for table in tables:
            print(f"  {table[0]}")

if __name__ == "__main__":
    check_schema()