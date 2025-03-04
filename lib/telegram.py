import requests
import const
from lib import cache, yandex_disk, forecasts_save, predictions_save, news_save, fundamentals_save, docker, counter, memcached
from lib.db import db_utils


def get_bot_url() -> str:
    return 'https://api.telegram.org/bot' + const.TELEGRAM_BOT_API_KEY


def send_message(message: str) -> None:
    try:
        for chat_id in const.TELEGRAM_CHAT_IDS:
            requests.post(
                get_bot_url() + '/sendMessage?chat_id=' + str(chat_id) + '&text=' + message,
            )
    except Exception as e:
        print('ERROR TELEGRAM send_message', e)


def get_updates(offset_update_id: int = None) -> list:
    try:
        res = requests.get(
            get_bot_url()
            + '/getUpdates'
            + (('?offset=' + str(offset_update_id)) if offset_update_id else '')
        )

        if res:
            json = res.json()

            if json and json['result'] and len(json['result']):
                return json['result']

    except Exception as e:
        print('ERROR TELEGRAM get_updates', e)

    return []


def process_updates() -> None:
    cache_key = 'telegram_offset_update_id'
    offset_update_id = cache.cache_get(cache_key)
    updates = get_updates(offset_update_id=offset_update_id)

    for u in updates:
        update_id = u['update_id']
        text = u['message']['text'].lower()
        cache.cache_set(cache_key, update_id)

        if update_id != offset_update_id:
            process_single_update(text)


def process_single_update(text: str = None) -> None:
    print('PROCESS TELEGRAM TASK', text)

    if text == 'backup':
        yandex_disk.upload_db_backup()

    elif text == 'forecasts':
        forecasts_save.save_forecasts()

    elif text == 'fundamentals':
        fundamentals_save.save_fundamentals()

    elif text == 'predictions':
        predictions_save.save_predictions()

    elif text == 'news':
        news_save.save_news()

    elif text == 'optimize':
        send_message('Начало оптимизации БД')
        db_utils.optimize_db()

    elif text == 'stat' or text == 'info':
        send_message('Сбор статистики')
        send_message('uptime')
        send_message(docker.get_uptime())
        send_message('df -h')
        send_message(docker.get_df())
        send_message('Счетчики')
        send_message(counter.get_stat())
        send_message('Статистика memcached')
        send_message(memcached.get_memcached_stats())

