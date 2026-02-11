import os

DATA_DIR = "/data"
DATA_FILE = os.path.join(DATA_DIR, "bot_data.pkl")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
