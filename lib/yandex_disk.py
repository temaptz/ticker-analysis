import os
import datetime
import requests
import json
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


class YandexDiskJSON:
    def __init__(self, disk_token: str, disk_file_path: str):
        """
        :param disk_token: OAuth-токен для доступа к Яндекс.Диску
        """
        self.disk_token = disk_token
        self.disk_file_path = disk_file_path
        self.base_url = "https://cloud-api.yandex.net/v1/disk"

    def _get_headers(self) -> dict:
        """
        Возвращает заголовки авторизации.
        """
        return {
            'Authorization': f'OAuth {self.disk_token}',
            'Content-Type': 'application/json'
        }

    @logger.error_logger
    def read_json(self) -> dict:
        # 1. Получаем ссылку для скачивания
        download_url = f'{self.base_url}/resources/download'
        params = {'path': self.disk_file_path}
        response = requests.get(download_url, headers=self._get_headers(), params=params)
        response.raise_for_status()  # выбросит исключение при неудачном запросе

        # 2. Получаем саму ссылку для скачивания из ответа
        download_href = response.json()['href']

        # 3. Загружаем содержимое напрямую в память
        file_response = requests.get(download_href)
        file_response.raise_for_status()

        # 4. Превращаем содержимое (строку JSON) в Python-словарь
        data = json.loads(file_response.text)

        return data

    @logger.error_logger
    def write_json(self, disk_path: str, data: dict):
        # Превращаем словарь в JSON-строку
        json_content = json.dumps(data, ensure_ascii=False, indent=2)

        # Получаем ссылку для загрузки
        upload_url = f'{self.base_url}/resources/upload'
        params = {
            'path': disk_path,
            'overwrite': 'true'
        }
        response = requests.get(upload_url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        # Достаём href из ответа
        upload_href = response.json()['href']

        # Загружаем напрямую из памяти, не сохраняя во временный файл
        upload_response = requests.put(
            upload_href,
            data=json_content.encode('utf-8')  # передаём байтовую строку напрямую
        )
        upload_response.raise_for_status()
