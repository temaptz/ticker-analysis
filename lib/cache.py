from functools import wraps
from lib import utils, redis_utils, logger, serializer


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
    logger.log_info(message='CACHE CLEAN')

    try:
        redis_utils.clear_cache()
    except Exception as e:
        print('ERROR cache clean', e)


def ttl_cache(ttl: int = 3600, is_skip_empty: bool = False, is_convert_object: bool = False):
    """Декоратор кэширования с временем жизни (ttl) и ограничением по размеру."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                key_md5 = utils.get_md5(f'{func.__module__}.{func.__name__}:{args}:{kwargs}_')
                saved_cache = cache_get(key=key_md5)

                if saved_cache:
                    return saved_cache  # Возвращаем из кэша, если есть

                result = func(*args, **kwargs)  # Вычисляем функцию

                if not is_skip_empty or result:
                    if is_convert_object:
                        if dict_by_object := serializer.get_dict_by_object_recursive(result):
                            if object_by_dict := serializer.dict_to_object_recursive(dict_by_object):
                                cache_set(key=key_md5, value=object_by_dict, ttl=ttl)
                    else:
                        cache_set(key=key_md5, value=result, ttl=ttl)

                return result

            except Exception as e:
                print(f'ERROR ttl_cache decorator in function {func.__name__}', e)

        return wrapper
    return decorator
