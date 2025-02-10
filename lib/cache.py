from cachetools import LRUCache

cache = LRUCache(maxsize=10000)

def get(key: str):
    return cache.get(key)

def set(key: str, value: any):
    cache[key] = value
