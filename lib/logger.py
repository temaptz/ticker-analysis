import datetime
from lib import docker, telegram

def log_error(method_name: str, error: Exception = None) -> None:
    date_str = datetime.datetime.now().strftime('')
    error_str = f'[{date_str}] ERROR: {method_name}'

    if error:
        error_str += f' -> {error}'

    print(error_str)

    if docker.is_prod():
        telegram.send_message(error_str)
