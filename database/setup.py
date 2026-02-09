#!/usr/bin/env python3
"""
Database Setup and Initialization Script
Applies the consolidated modern schema with all features included
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    """Initialize database with modern consolidated schema"""
    
    print("🗄️  Setting up NVIDIA Prediction Database...")
    
    # Database configuration (adjust as needed)
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'your_password',  # Update this
        'database': 'nvidia_prediction'
    }
    
    try:
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        print(f"📝 Creating database '{db_config['database']}'...")
        cursor.execute(f"DROP DATABASE IF EXISTS {db_config['database']}")
        cursor.execute(f"CREATE DATABASE {db_config['database']}")
        
        cursor.close()
        conn.close()
        
        # Connect to the new database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Execute the consolidated schema
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        print(f"📋 Applying consolidated schema from {schema_path}...")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Database setup complete!")
        print("📊 Features included:")
        print("   • Macro sentiment separation (company vs macro articles)")
        print("   • Opening gap prediction support")
        print("   • Gravity accuracy system with letter grades")
        print("   • No foreign key constraints (weekend articles supported)")
        print("   • Enhanced views with modern analytics")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
