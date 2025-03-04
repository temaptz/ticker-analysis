from enum import Enum
from lib import cache


class Counters(Enum):
    YANDEX_GPT_TEXT_REQUEST = '1'
    YANDEX_GPT_NEWS_CLASSIFY = '2'
    YANDEX_CACHED_REQUEST = '3'
    NEWS_RATE_NEW = '4'
    NEWS_RATE_DB = '5'
    NEWS_GET_COUNT = '6'


counters = dict()


def increment(counter_name: str or Counters) -> None:
    key = str(counter_name)

    if key not in counters:
        counters[key] = cache.cache_get(key=key) or 0

    counters[key] += 1
    cache.cache_set(key=key, value=counters[key])


def get(counter_name: str or Counters) -> int:
    key = str(counter_name)

    if key not in counters:
        return cache.cache_get(key=key) or 0

    return counters[key]


def get_stat() -> str:
    return f'''
        [TOTAL STAT START]
        YANDEX_GPT_TEXT_REQUEST = {get(Counters.YANDEX_GPT_TEXT_REQUEST)}\n
        YANDEX_GPT_NEWS_CLASSIFY = {get(Counters.YANDEX_GPT_NEWS_CLASSIFY)}\n
        YANDEX_CACHED_REQUEST = {get(Counters.YANDEX_CACHED_REQUEST)}\n
        NEWS_RATE_NEW = {get(Counters.NEWS_RATE_NEW)}\n
        NEWS_RATE_DB = {get(Counters.NEWS_RATE_DB)}\n
        NEWS_GET_COUNT = {get(Counters.NEWS_GET_COUNT)}\n
        [TOTAL STAT END]\n
        '''
