import math

import numpy
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._models.text_classifiers.model import FewShotTextClassifiersModelResult
import const
from lib import utils, cache
from decimal import Decimal


# Функция для отправки текстового запроса к GPT и получения ответа
def get_gpt_text(text_query: str) -> str:
    try:
        sdk = YCloudML(
            auth=const.Y_API_SECRET,
            folder_id=const.Y_API_FOLDER_ID
        )

        model = sdk.models.completions('yandexgpt')
        model = model.configure(temperature=0.5)

        result = model.run(text_query)

        return result.alternatives[0].text

    except Exception as e:
        print('ERROR get_gpt_text', e)
        return ''


def get_text_classify(title: str, text: str, subject_name: str) -> int:
    try:
        sdk = YCloudML(
            auth=const.Y_API_SECRET,
            folder_id=const.Y_API_FOLDER_ID
        )

        # Объединение заголовка и текста новости
        news_text = f"{title}\n\n{text}"

        # Формирование описания задачи с учетом названия компании
        task_description = (
            f"Оцените экономическое влияние следующей новости на компанию {subject_name}:"
        )

        # Примеры для Few-shot обучения
        samples = [
            {
                "text": f"Компания {subject_name} объявила о сокращении 500 сотрудников из-за падения продаж.",
                "label": "отрицательное влияние"
            },
            {
                "text": f"Компания {subject_name} выпустила новый продукт, который получил положительные отзывы.",
                "label": "положительное влияние"
            },
            {
                "text": f"Компания {subject_name} провела ежегодное собрание акционеров без значимых объявлений.",
                "label": "нейтральное влияние"
            }
        ]

        # Настройка модели классификации
        model = sdk.models.text_classifiers('yandexgpt').configure(
            task_description=task_description,
            labels=['положительное влияние', 'отрицательное влияние', 'нейтральное влияние'],
            samples=samples
        )

        result: FewShotTextClassifiersModelResult = model.run(news_text)

        if result and len(result) >= 3:
            largest = sorted(result, key=lambda item: utils.round_float(item.confidence))[-1]

            if 'положительное' in largest.label:
                return 1

            if 'отрицательное' in largest.label:
                return -1

        return 0

    except Exception as e:
        print('ERROR get_gpt_text', e)
        return 0


@cache.ttl_cache()
def get_human_name(legal_name: str) -> str:
    return get_gpt_text('Какое краткое общепринятое название этой компании: "'+legal_name+'"?')
