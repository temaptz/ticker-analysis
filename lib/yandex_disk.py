import os
import datetime
import requests
import urllib.parse
import const
from lib import telegram, utils, logger
from lib.db_2 import db_utils, backup


@logger.error_logger
def upload_db_backup() -> None:
    print('START BACKUP')
    telegram.send_message('Начало резервного копирования')

    db_utils.optimize_db()

    db_dump_file_name = f'db_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.dump'
    db_dump_file_path = db_dump_file_name

    file_path_on_ya_disk = f'/ticker-analysis-backup/{db_dump_file_name}'

    url_resource = 'https://cloud-api.yandex.net/v1/disk/resources/upload?%s' % urllib.parse.urlencode({
        'path': file_path_on_ya_disk
    })

    response_resource = requests.get(
        url_resource,
        headers={'Authorization': 'OAuth %s' % const.Y_DISK_TOKEN}
    ).json()

    backup.backup_database(dump_file_path=db_dump_file_path)

    with open(db_dump_file_path, 'rb') as file:
        file_size = utils.get_file_size_readable(filepath=db_dump_file_path)
        print('FILE CREATED, BEFORE BACKUP UPLOAD', file_size)
        response_upload = requests.put(response_resource['href'], files={'file': file})

        print('RESPONSE UPLOAD', response_upload.status_code, response_upload.text, response_upload)

        if response_upload:
            print('BACKUP UPLOADED', response_upload.status_code, file_path_on_ya_disk)

            telegram.send_message('Резервное копирование успешно завершено с кодом: '+str(response_upload.status_code)+'. Создан файл: '+file_path_on_ya_disk+' Размер: '+file_size)

    os.remove(db_dump_file_path)
