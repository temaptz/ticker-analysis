import requests
import const
from lib import cache, yandex_disk, forecasts_save, predictions_save, news_save, fundamentals_save
from lib.db import db_utils


def get_bot_url() -> str:
    return 'https://api.telegram.org/bot' + const.TELEGRAM_BOT_API_KEY


def send_message(message: str) -> None:
    for chat_id in const.TELEGRAM_CHAT_IDS:
        requests.post(
            get_bot_url() + '/sendMessage?chat_id=' + str(chat_id) + '&text=' + message,
        )


def get_updates(offset_update_id: int = None) -> list:
    res = requests.get(
        get_bot_url()
        + '/getUpdates'
        + (('?offset=' + str(offset_update_id)) if offset_update_id else '')
    )

    if res:
        json = res.json()

        if json and json['result'] and len(json['result']):
            return json['result']

    return []


def process_updates() -> None:
    cache_key = 'telegram_offset_update_id'
    offset_update_id = cache.get(cache_key)
    updates = get_updates(offset_update_id=offset_update_id)

    for u in updates:
        update_id = u['update_id']
        text = u['message']['text']
        cache.set(cache_key, update_id)

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
        db_utils.optimize_db()

