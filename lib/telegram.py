import requests
import const
from lib import docker


def get_bot_url() -> str:
    return 'https://api.telegram.org/bot' + const.TELEGRAM_BOT_API_KEY


def send_message(message: str) -> None:
    if not docker.is_prod():
        return

    try:
        for chat_id in const.TELEGRAM_CHAT_IDS:
            requests.post(
                get_bot_url() + '/sendMessage?chat_id=' + str(chat_id) + '&text=' + message,
            )
            print('TELEGRAM SENT MESSAGE', message)
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
