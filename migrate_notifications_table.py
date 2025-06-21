import sqlite3

db_path = "buying_group_deals.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check if batch_id column exists
c.execute("PRAGMA table_info(notifications)")
columns = [row[1] for row in c.fetchall()]
if "batch_id" not in columns:
    print("Adding batch_id column to notifications table...")
    c.execute("ALTER TABLE notifications ADD COLUMN batch_id TEXT")
    conn.commit()
else:
    print("batch_id column already exists.")

conn.close()
print("Migration complete.") 