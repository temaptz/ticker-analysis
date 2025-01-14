from django.core.cache import cache

def get(key: str):
    return cache.get(key)

def set(key: str, value: any):
    cache.set(key, value)
