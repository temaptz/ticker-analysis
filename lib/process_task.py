from lib import cache, yandex_disk, forecasts_save, predictions_save, news_save, fundamentals_save, docker, counter, redis_utils, telegram
from lib.db_2 import db_utils


def process_updates() -> None:
    cache_key = 'telegram_offset_update_id'
    offset_update_id = cache.cache_get(cache_key)
    updates = telegram.get_updates(offset_update_id=offset_update_id)
    for u in updates:
        update_id = u['update_id']
        text = u['message']['text'].lower()
        cache.cache_set(cache_key, update_id)
        if update_id != offset_update_id:
            print('TELEGRAM UPDATE_ID', update_id)
            print('TELEGRAM UPDATE_TEXT', text)
            process_single_update(text)


def process_single_update(text: str = None) -> None:
    print('PROCESS TELEGRAM TASK', text)

    if text == '/backup':
        yandex_disk.upload_db_backup()

    elif text == '/forecasts':
        forecasts_save.save_forecasts()

    elif text == '/fundamentals':
        fundamentals_save.save_fundamentals()

    elif text == '/predictions':
        predictions_save.save_predictions()

    elif text == '/news':
        news_save.save_news()

    elif text == '/optimize':
        telegram.send_message('Начало оптимизации БД')
        db_utils.optimize_db()

    elif text == '/stat':
        telegram.send_message('Сбор статистики')
        telegram.send_message('uptime')
        telegram.send_message(docker.get_uptime())
        telegram.send_message('df -h')
        telegram.send_message(docker.get_df())
        telegram.send_message('Счетчики')
        telegram.send_message(counter.get_stat())
        telegram.send_message('Статистика redis')
        telegram.send_message(redis_utils.get_redis_stats())

    elif text == '/cache':
        telegram.send_message('Очистка кэша')
        cache.clean()
