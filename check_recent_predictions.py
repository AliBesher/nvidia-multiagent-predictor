from data.database_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'recent_predictions' ORDER BY column_name;")
    columns = cursor.fetchall()
    print("recent_predictions columns:")
    for col in columns:
        print(f"  {col[0]}")