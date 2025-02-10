import os
import datetime
import requests
import urllib.parse
import const
from lib import (telegram, utils)


def upload_db_backup() -> None:
    try:
        print('START BACKUP')
        telegram.send_message('Начало резервного копирования')

        file_path_on_disk = (
                '/ticker-analysis-backup/'
                + os.path.splitext(os.path.basename(const.DB_FILENAME))[0]
                + '_'
                + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
                + os.path.splitext(os.path.basename(const.DB_FILENAME))[1]
        )

        url_resource = 'https://cloud-api.yandex.net/v1/disk/resources/upload?%s' % urllib.parse.urlencode({
            'path': file_path_on_disk
        })

        response_resource = requests.get(
            url_resource,
            headers={'Authorization': 'OAuth %s' % const.Y_DISK_TOKEN}
        ).json()

        file_abspath = utils.get_file_abspath_recursive(const.DB_FILENAME)

        with open(file_abspath, 'rb') as file:
            response_upload = requests.put(response_resource['href'], files={'file': file})

            if response_upload:
                file_size = utils.get_file_size_readable(filepath=file_abspath)
                print('BACKUP UPLOADED', response_upload.status_code, file_path_on_disk)

                telegram.send_message('Резервное копирование успешно завершено с кодом: '+str(response_upload.status_code)+'. Создан файл: '+file_path_on_disk+' Размер: '+file_size)

    except Exception as e:
        print('ERROR YANDEX DISK BACKUP', e)
        telegram.send_message('Ошибка резервного копирования: '+str(e))
