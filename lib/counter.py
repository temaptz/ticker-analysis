from enum import Enum


class Counters(Enum):
    YANDEX_GPT_TEXT_REQUEST = '1'
    YANDEX_GPT_NEWS_CLASSIFY = '2'
    YANDEX_CACHED_REQUEST = '3'
    NEWS_RATE_NEW = '4'
    NEWS_RATE_DB = '5'
    NEWS_GET_COUNT = '6'


counters = dict()


def increment(counter_name: str or Counters) -> None:
    if counter_name not in counters:
        counters[counter_name] = 0

    counters[counter_name] += 1


def get(counter_name: str or Counters) -> int:
    if counter_name not in counters:
        return 0

    return counters[counter_name]


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
