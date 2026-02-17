from data.database_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # البحث عن أي أعمدة تحتوي على hybrid أو gravity
    cursor.execute("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE column_name ILIKE '%hybrid%' 
           OR column_name ILIKE '%gravity%'
           OR column_name ILIKE '%confidence%'
           OR column_name ILIKE '%strategy%'
           OR column_name ILIKE '%technical%'
        ORDER BY table_name, column_name
    """)
    
    columns = cursor.fetchall()
    print("Columns containing hybrid/gravity/confidence/strategy/technical:")
    current_table = None
    for col in columns:
        if col[0] != current_table:
            print(f"\n{col[0]}:")
            current_table = col[0]
        print(f"  - {col[1]}")
    
    # البحث في جدول daily_data عن أي بيانات تحتوي على توقعات هايبريد
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'daily_data' 
        ORDER BY column_name
    """)
    
    all_columns = cursor.fetchall()
    print(f"\n\nAll daily_data columns ({len(all_columns)}):")
    for col in all_columns:
        print(f"  - {col[0]} ({col[1]})")