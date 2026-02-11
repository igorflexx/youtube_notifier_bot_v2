import sqlite3
from datetime import datetime

DB_PATH = "/data/database.db"  # Путь для Railway volume
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если их нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    name TEXT,
    last_video TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER,
    channel_id TEXT,
    PRIMARY KEY(user_id, channel_id),
    FOREIGN KEY(channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE
)
""")
conn.commit()

# Получить список каналов пользователя
def get_user_channels(user_id):
    cursor.execute("""
    SELECT c.name, c.channel_id
    FROM channels c
    JOIN subscriptions s ON c.channel_id = s.channel_id
    WHERE s.user_id = ?
    """, (user_id,))
    return cursor.fetchall()

# Удалить канал у пользователя (только связь)
def remove_channel(user_id, channel_id):
    cursor.execute("""
    DELETE FROM subscriptions
    WHERE user_id=? AND channel_id=?
    """, (user_id, channel_id))
    conn.commit()
