import sqlite3

DATABASE_NAME = "grocery.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        weight REAL NOT NULL,
        quantity INTEGER DEFAULT 1,
        date_added TEXT,
        last_updated TEXT,
        status TEXT DEFAULT 'Available'
    )
    """
    )

    conn.commit()
    conn.close()
