import requests
import const


def get_bot_url() -> str:
    return 'https://api.telegram.org/bot' + const.TELEGRAM_BOT_API_KEY


def send_message(message: str) -> None:
    for chat_id in const.TELEGRAM_CHAT_IDS:
        requests.post(
            get_bot_url() + '/sendMessage?chat_id=' + str(chat_id) + '&text=' + message,
        )


def get_updates(offset_update_id: int = None) -> list:
    print(get_bot_url()
          + '/getUpdates'
          + (('?offset=' + str(offset_update_id)) if offset_update_id else ''))

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
