import re
from html import unescape
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._models.text_classifiers.model import FewShotTextClassifiersModelResult
import const
from lib import utils, cache, counter, logger, serializer, types, docker, throttle_decorator
from lib.db_2 import gpt_requests_db, news_classify_requests


#  Функция для отправки текстового запроса к GPT и получения ответа
def get_gpt_text(text_query: str, instruction: str = '') -> str or None:
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

            return result

    except Exception as e:
        logger.log_error(method_name='get_gpt_text', error=e)

    return None


def get_text_classify_db_cache(title: str, text: str, subject_name: str) -> FewShotTextClassifiersModelResult or None:
    try:
        cached = news_classify_requests.get_model_result_by_record(
            record=news_classify_requests.get_classify(
                news_hash=news_classify_requests.get_news_hash(
                    news_title=title,
                    news_text=text,
                ),
                subject_name=subject_name,
            )
        )

        if cached:
            return cached
    except Exception as e:
        logger.log_error(method_name='get_text_classify_db_cache_[GETTING CACHE]', error=e)

    if const.IS_NEWS_CLASSIFY_ENABLED and docker.is_prod():
        ya_classify = get_text_classify(title=title, text=text, subject_name=subject_name)

        if ya_classify is not None:
            result = serializer.get_dict_by_object_recursive(ya_classify)

            news_classify_requests.insert_classify(
                news_hash=news_classify_requests.get_news_hash(
                    news_title=title,
                    news_text=text,
                ),
                subject_name=subject_name,
                classify=result,
            )

            logger.log_info(
                message='NEWS RATED BY YANDEX',
                output={
                    'rate': serializer.get_dict_by_object_recursive(
                        data=get_news_rate_absolute_by_ya_classify(result)
                    ),
                    'result': result,
                },
            )

            return result

    return None


@throttle_decorator.throttle_once_per_second
def get_text_classify(title: str, text: str, subject_name: str) -> FewShotTextClassifiersModelResult or None:
    try:
        sdk = YCloudML(
            auth=const.Y_API_SECRET,
            folder_id=const.Y_API_FOLDER_ID
        )

        # Объединение заголовка и текста новости
        news_text = clean_news_text(text=f'{title}\n{text}')
        labels = ['положительная', 'отрицательная', 'нейтральная']
        labels_str = ', '.join([f'"{label}"' for label in labels])

        # Формирование описания задачи с учетом названия компании
        task_description = (f'''
                Я передам тебе новость, которая связана с организацией "{subject_name}". 
                Твоя задача — классифицировать эту новость как {labels_str} 
                в контексте того, как она может отразиться на стоимости ценных бумаг организации. 
                
                При классификации учитывай, как новость:
                — влияет на финансовые показатели и рыночную капитализацию;
                — изменяет общее восприятие и репутацию организации среди инвесторов;
                — соотносится с текущими рыночными тенденциями и конкурентной средой;
                — может повлиять на спрос и предложение на рынке акций.
            ''')

        # Настройка модели классификации
        model = sdk.models.text_classifiers(model_name='yandexgpt-lite', model_version='latest').configure(
            task_description=task_description,
            labels=['положительная', 'отрицательная', 'нейтральная'],
        )

        ya_resp: FewShotTextClassifiersModelResult = model.run(news_text)

        if ya_resp and len(ya_resp) >= 3 and get_news_rate_absolute_by_ya_classify(classify=serializer.get_dict_by_object_recursive(ya_resp)) is not None:
            return ya_resp

    except Exception as e:
        logger.log_error(method_name='get_text_classify', error=e, debug_info=serializer.to_json({
            'title_cat_50': title[:50],
            'text_cat_50': text[:50],
            'subject_name': subject_name,
        }, ensure_ascii=False))

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
        + 'Пример 1: Запрос - Сбер Банк - привилегированные акции Ответ: Сбербанк\n'
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
            + 'Пример 1: Запрос - Сбер Банк - привилегированные акции Ответ: сбер;сбербанк\n'
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


def get_news_rate_by_ya_classify(classify: dict) -> types.NewsRate or None:
    abs_classify: types.NewsRateAbsoluteYandex = get_news_rate_absolute_by_ya_classify(classify=classify)

    if abs_classify:
        result = types.NewsRate(0, 0, 0)
        total_sum = abs_classify.positive_total + abs_classify.negative_total + abs_classify.neutral_total

        result.positive_percent = utils.round_float(num=abs_classify.positive_total / total_sum * 100, decimals=5)
        result.negative_percent = utils.round_float(num=abs_classify.negative_total / total_sum * 100, decimals=5)
        result.neutral_percent = utils.round_float(num=abs_classify.neutral_total / total_sum * 100, decimals=5)

        return result

    return None


def get_news_rate_absolute_by_ya_classify(classify: dict) -> types.NewsRateAbsoluteYandex or None:
    if classify and 'predictions' in classify:
        sum_confidence = utils.round_float(
            num=sum(utils.round_float(num=i['confidence'], decimals=10) for i in classify['predictions']),
            decimals=5,
        )

        if sum_confidence > 0 and len(classify['predictions']) == 3:
            result = types.NewsRateAbsoluteYandex(0, 0, 0)

            for i in classify['predictions']:
                value = utils.round_float(
                    num=i['confidence'],
                    decimals=5,
                )

                if i['label'] == 'положительная':
                    result.positive_total = value
                elif i['label'] == 'отрицательная':
                    result.negative_total = value
                elif i['label'] == 'нейтральная':
                    result.neutral_total = value

            return result

    return None


def clean_news_text(text: str, max_chars: int = 28000) -> str or None:
    if not isinstance(text, str):
        return None

    # Удаление base64 inline изображений
    text = re.sub(r'<img[^>]+src=["\']data:image/[^"\']+["\'][^>]*>', '', text, flags=re.IGNORECASE)

    # Удаление всех остальных HTML-тегов
    text = re.sub(r'<[^>]+>', '', text)

    # Преобразование HTML-сущностей в нормальные символы
    text = unescape(text)

    # Удаление лишних пробелов и переносов строк
    text = re.sub(r'\s+', ' ', text).strip()

    # Усечём текст до лимита символов (ориентировочно <8000 токенов)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0]  # чтобы не обрывать слово посередине

    return text
