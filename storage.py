import os
import json

def load_channels(file_path: str) -> list:
    """Загружает список каналов из файла."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_channels(file_path: str, channels: list):
    """Сохраняет список каналов в файл, создавая папку если нужно."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)
