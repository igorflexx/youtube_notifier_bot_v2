import sqlite3

DB_PATH = "/data/database.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Таблица каналов
cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT,
    last_video_id TEXT,
    last_notified_video_id TEXT
)
""")

# Таблица подписок
cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER,
    channel_id TEXT,
    UNIQUE(user_id, channel_id)
)
""")

conn.commit()

# -----------------------------
# Функции работы с каналами
# -----------------------------

def remove_channel(user_id, channel_id):
    cursor.execute(
        "DELETE FROM subscriptions WHERE user_id=? AND channel_id=?",
        (user_id, channel_id)
    )
    conn.commit()

def get_user_channels(user_id):
    cursor.execute("""
    SELECT c.channel_name, c.channel_id
    FROM channels c
    JOIN subscriptions s ON c.channel_id=s.channel_id
    WHERE s.user_id=?
    """, (user_id,))
    return cursor.fetchall()
