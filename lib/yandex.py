from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._models.text_classifiers.model import FewShotTextClassifiersModelResult
import const
from lib import utils, cache, counter
from lib.db import gpt_requests_db


class NewsRate:
    def __init__(self, positive_percent=0, negative_percent=0, neutral_percent=0):
        self.positive_percent = positive_percent
        self.negative_percent = negative_percent
        self.neutral_percent = neutral_percent


#  Функция для отправки текстового запроса к GPT и получения ответа
def get_gpt_text(text_query: str, instruction: str = '') -> str:
    try:
        db_request = 'User: '+text_query+' System: '+instruction
        db_response = gpt_requests_db.get_response(request=db_request)
        if db_response:
            print('GPT SAVED DB TEXT RESPONSE', db_response)
            counter.increment(counter.Counters.YANDEX_CACHED_REQUEST)
            return db_response

        sdk = YCloudML(
            auth=const.Y_API_SECRET,
            folder_id=const.Y_API_FOLDER_ID
        )

        model = sdk.models.completions('yandexgpt').configure(temperature=0)

        messages = [{
            'role': 'user',
            'text': text_query
        }]

        if instruction:
            messages.insert(0, {
                'role': 'system',
                'text': instruction
            })

        counter.increment(counter.Counters.YANDEX_GPT_TEXT_REQUEST)

        result = model.run(messages).alternatives[0].text

        if result:
            gpt_requests_db.insert_response(request=db_request, response=result)

        print('GPT TEXT RESPONSE', result)

        return result

    except Exception as e:
        print('ERROR get_gpt_text', e)
        return ''


def get_text_classify(title: str, text: str, subject_name: str) -> int or None:
    try:
        sdk = YCloudML(
            auth=const.Y_API_SECRET,
            folder_id=const.Y_API_FOLDER_ID
        )

        # Объединение заголовка и текста новости
        news_text = f"{title}\n\n{text}"

        # Формирование описания задачи с учетом названия компании
        task_description = (
            f"Оцени экономическое влияние следующей новости на компанию {subject_name}:"
        )

        # Настройка модели классификации
        model = sdk.models.text_classifiers('yandexgpt').configure(
            task_description=task_description,
            labels=['положительное влияние', 'отрицательное влияние', 'нейтральное влияние'],
            samples=get_news_rate_samples(instrument_name=subject_name)
        )

        print('GPT REQUEST', task_description)

        counter.increment(counter.Counters.YANDEX_GPT_NEWS_CLASSIFY)

        result: FewShotTextClassifiersModelResult = model.run(news_text)

        if result and len(result) >= 3:
            largest = sorted(result, key=lambda item: utils.round_float(item.confidence))[-1]

            if 'положительное' in largest.label:
                return 1
            elif 'отрицательное' in largest.label:
                return -1
            elif 'нейтральное' in largest.label:
                return 0

    except Exception as e:
        print('ERROR get_text_classify', e)

    return None


def get_text_classify_2(title: str, text: str, subject_name: str) -> int or None:
    try:
        sdk = YCloudML(
            auth=const.Y_API_SECRET,
            folder_id=const.Y_API_FOLDER_ID
        )

        # Объединение заголовка и текста новости
        news_text = f"{title}\n\n{text}"

        # Формирование описания задачи с учетом названия компании
        task_description = (
            f'Я передам тебе новость имеющую отношение к организации {subject_name}. '
            f'Классифицируй ее, в контексте этой организации, на: положительную, отрицательную, нейтральную'
        )

        # Настройка модели классификации
        model = sdk.models.text_classifiers('yandexgpt-lite').configure(
            task_description=task_description,
            labels=['положительная', 'отрицательная', 'нейтральная'],
        )

        print('GPT REQUEST CLASSIFY', subject_name, title)

        counter.increment(counter.Counters.YANDEX_GPT_NEWS_CLASSIFY)

        result: FewShotTextClassifiersModelResult = model.run(news_text)

        if result and len(result) >= 3:
            largest = sorted(result, key=lambda item: utils.round_float(item.confidence))[-1]

            if 'положительная' in largest.label:
                return 1
            elif 'отрицательная' in largest.label:
                return -1
            elif 'нейтральная' in largest.label:
                return 0

    except Exception as e:
        print('ERROR get_text_classify_2', e)

    return None


def get_text_classify_3(title: str, text: str, subject_name: str) -> NewsRate or None:
    try:
        sdk = YCloudML(
            auth=const.Y_API_SECRET,
            folder_id=const.Y_API_FOLDER_ID
        )

        # Объединение заголовка и текста новости
        news_text = f'{title}\n{text}'

        # Формирование описания задачи с учетом названия компании
        task_description = (f'''
            Я передам тебе новость, имеющую отношение к организации "{subject_name}". 
            Твоя задача — классифицировать её на положительную, отрицательную или нейтральную 
            в контексте этой организации. 
            При классификации учитывай перспективы развития, повышение финансовых показателей, 
            общую репутацию компании, рыночные тенденции и конкурентную среду. 
            Ответ должен быть кратким и содержать только классификацию новости.
        ''')

        # Настройка модели классификации
        model = sdk.models.text_classifiers('yandexgpt-lite').configure(
            task_description=task_description,
            labels=['положительная', 'отрицательная', 'нейтральная'],
        )

        counter.increment(counter.Counters.YANDEX_GPT_NEWS_CLASSIFY)

        ya_resp: FewShotTextClassifiersModelResult = model.run(news_text)

        if ya_resp and len(ya_resp) >= 3:
            result = NewsRate()
            sum_confidence = utils.round_float(
                num=sum(utils.round_float(num=i.confidence, decimals=10) for i in ya_resp),
                decimals=5,
            )

            for i in ya_resp:
                round_confidence = utils.round_float(
                    num=i.confidence,
                    decimals=5,
                )
                percent = utils.round_float(
                    num=round_confidence / sum_confidence * 100,
                    decimals=5,
                )

                if i.label == 'положительная':
                    result.positive_percent = percent
                elif i.label == 'отрицательная':
                    result.negative_percent = percent
                elif i.label == 'нейтральная':
                    result.neutral_percent = percent

            return result

    except Exception as e:
        print('ERROR get_text_classify_3', e)

    return None


# Возвращает распространенное в обиходе название
@cache.ttl_cache(ttl=3600 * 24 * 30)
def get_human_name(legal_name: str) -> str:
    instruction = (
        'Ты эксперт в области бизнеса, финансов и журналистики. '
        + 'Я говорю тебе как называется сущность, а ты находишь публичное, краткое, распространенное, '
        + 'общепринятое название этой сущности, которое чаще всего встречается в российских СМИ '
        + 'и будет лучше всего понятно большинству людей. '
        + 'Ответ должен содержать только одно название, которое однозначно идентифицирует сущность.\n'
        + 'Пример 1: Запрос - Сбер Банк - привилегированные акции Ответ: Сбер Банк\n'
        + 'Пример 2: Запрос - Норильский никель Ответ: Норильский никель\n'
        + 'Пример 3: Запрос - ФСК Россети Ответ: ФСК Россети\n'
        + 'Пример 4: Запрос - Fix Price Group Ответ: FixPrice\n'
        + 'Пример 5: Запрос - Ozon Holdings PLC Ответ: Озон\n'
        + 'Пример 6: Запрос - Группа Позитив Ответ: Positive Technologies\n'
        + 'Пример 7: Запрос - МГТС - акции привилегированные Ответ: МГТС\n'
    )

    return (
        get_gpt_text(text_query=legal_name, instruction=instruction)
        .replace('"', '')
        .strip('.')
    )


# Возвращает массив ключевых слов для поиска по названию
@cache.ttl_cache(ttl=3600 * 24 * 30)
def get_keywords(legal_name: str) -> list[str]:
    result = list()
    instruction = (
            'Ты эксперт в области бизнеса, финансов и журналистики. '
            + 'Я говорю тебе как называется сущность, а ты придумываешь краткое, распространенное, '
            + 'общепринятое название этой сущности, которое чаще всего встречается в российских СМИ '
            + 'и будет лучше всего понятно большинству людей. '
            + 'Если таких названий несколько, то напиши их через точку с запятой.\n'
            + 'Пример 1: Запрос - Сбер Банк - привилегированные акции Ответ: сбер;сбербанк;сбер банк\n'
            + 'Пример 2: Запрос - Магнит Ответ: магнит\n'
            + 'Пример 3: Запрос - Норильский никель Ответ: норильский никель;норникель\n'
            + 'Пример 4: Запрос - Аэрофлот Ответ: аэрофлот\n'
            + 'Пример 5: Запрос - Северсталь Ответ: северсталь\n'
            + 'Пример 6: Запрос - ФСК Россети Ответ: фск россети;россети\n'
            + 'Пример 7: Запрос - Ozon Holdings PLC Ответ: озон;ozon\n'
            + 'Пример 8: Запрос - МТС Ответ; мтс;мобильные телесистемы\n'
            + 'Пример 9: Запрос - Fix Price Group Ответ: фикс прайс;fix price\n'
            + 'Пример 10: Запрос - Группа Позитив Ответ: positive technologies\n'
            + 'Пример 11: Запрос - МГТС - акции привилегированные Ответ: мгтс\n'
            + 'Пример 12: Запрос - ФосАгро Ответ: фосагро\n'
            + 'Пример 13: Запрос - HeadHunter Group PLC Ответ: headhunter;hh.ru\n'
            + 'Пример 14: Запрос - Эн+ Ответ: эн+\n'
    )

    response = (
        get_gpt_text(text_query=legal_name, instruction=instruction)
        .strip('.')
        .replace('"', '')
        .lower()
    )

    for word in [i.strip() for i in response.split(';')]:
        if word not in result:
            result.append(word)

    return result


# Примеры для Few-shot обучения
def get_news_rate_samples(instrument_name: str):
    return [
        {
            "text": f"Компания {instrument_name} выпустила новый продукт, который получил положительные отзывы.",
            "label": "положительное влияние"
        },
        {
            "text": f"Лучшую динамику в ходе торгов демонстрируют акции {instrument_name}",
            "label": "положительное влияние"
        },
        {
            "text": f"Компания {instrument_name} объявила о сокращении 500 сотрудников из-за падения продаж.",
            "label": "отрицательное влияние"
        },
        {
            "text": f"Сильнее остальных просели бумаги {instrument_name}",
            "label": "отрицательное влияние"
        },
        {
            "text": f"Прибыль от продаж упала",
            "label": "отрицательное влияние"
        },
        {
            "text": f"Выручка снизилась",
            "label": "отрицательное влияние"
        },
        {
            "text": f"Компания {instrument_name} провела ежегодное собрание акционеров без значимых объявлений.",
            "label": "нейтральное влияние"
        },
    ]
