import time
from cachetools import LRUCache

cache = LRUCache(maxsize=100)
expirations = {}


def get(key: str):
    if key in cache and time.time() < expirations.get(key, 0):
        return cache[key]
    cache.pop(key, None)  # Удаляем устаревший ключ
    expirations.pop(key, None)
    return None


def set(key: str, value: any, ttl: int = 3600) -> None:
    cache[key] = value
    expirations[key] = time.time() + ttl
