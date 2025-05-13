from functools import wraps
from lib import utils, redis_utils


def cache_get(key: str):
    try:
        return redis_utils.cache_get(key=key)
    except Exception as e:
        print('ERROR cache_get', e)

    return None


def cache_set(key: str, value: any, ttl: int = 3600) -> None:
    try:
        redis_utils.cache_set(key=key, value=value, ttl_sec=ttl)
    except Exception as e:
        print('ERROR cache_set', e)


def clean():
    try:
        redis_utils.flush_all()
    except Exception as e:
        print('ERROR cache clean', e)


def ttl_cache(ttl: int = 3600, maxsize: int = 1024, skip_empty: bool = False):
    """Декоратор кэширования с временем жизни (ttl) и ограничением по размеру."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                key_md5 = utils.get_md5(f'{func.__module__}.{func.__name__}:{args}:{kwargs}')
                saved_cache = cache_get(key=key_md5)

                if saved_cache:
                    return saved_cache  # Возвращаем из кэша, если есть

                result = func(*args, **kwargs)  # Вычисляем функцию

                if not skip_empty or result:
                    cache_set(key=key_md5, value=result, ttl=ttl)  # Сохраняем в кэше

                return result

            except Exception as e:
                print('ERROR ttl_cache decorator', e)

        return wrapper
    return decorator
