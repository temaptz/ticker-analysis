import re
import time

from lib.db_2 import news_db
from lib import instruments, yandex, cache, counter, docker, serializer, utils, logger, types, local_llm


@logger.error_logger
def get_news_rate(
        news_uid: list[str],
        subject_name: str,
) -> types.NewsRate2 or None:
    news = []
    for i in news_uid:
        n = news_db.get_news_by_uid(news_uid=i)
        if n:
            news.append(n)

    if len(news) > 0:
        for i in news:
            rate = get_text_rate(
                text=utils.clean_news_text_for_llm(title=i.title, text=i.text),
                subject_name=subject_name,
            )

            if rate and rate.is_ready():
                return rate

    return None


@logger.error_logger
def get_text_rate(text: str, subject_name: str) -> types.NewsRate2 or None:
    # print('------------------------------------------------------------------')
    # print('GPT REQUEST\n', get_prompt(news_text=text, subject_name=subject_name))

    resp: types.LocalLlmResponse or None = local_llm.generate(
        prompt=get_prompt(news_text=text, subject_name=subject_name)
    )

    if resp:
        sentiment = parse_rate_param(text=resp['response'], param_name='sentiment')
        impact_strength = parse_rate_param(text=resp['response'], param_name='impact_strength')
        mention_focus = parse_rate_param(text=resp['response'], param_name='mention_focus')

        # print('GPT RESPONSE\n', resp)
        # print('------------------------------------------------------------------')
        # print('GPT PARAM PARSED sentiment', sentiment)
        # print('GPT PARAM PARSED impact_strength', impact_strength)
        # print('GPT PARAM PARSED mention_focus', mention_focus)
        # print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')

        rate = types.NewsRate2(
            sentiment=sentiment,
            impact_strength=impact_strength,
            mention_focus=mention_focus,
            llm_response=resp,
        )

        if rate and rate.is_ready():
            return rate

    return None


def get_prompt(subject_name: str, news_text: str) -> str:
    return f'''
Ты — финансовый аналитик. Оцени следующую новость относительно её влияния на стоимость акций компании {subject_name}.

Заполни три признака:

1. sentiment — тон новости относительно компании (от -1.00 - отрицательный до +1.00 - положительный)
2. impact_strength — сила потенциального влияния на цену акций (от 0.00 - не влияет до 1.00 - сильно влияет)
3. mention_focus — насколько явно и подробно упоминается компания (от 0.00 - не упомянута до 1.00 - явно и подробно)

Ответ в формате:
sentiment: [значение]
impact_strength: [значение]
mention_focus: [значение]

Далее текст новости, которую нужно оценить:
{news_text}
'''


def parse_rate_param(text: str, param_name: str) -> float or None:
    if text:
        try:
            pattern = fr"{param_name}\s*:\s*(-?\d+(?:\.\d+)?)"
            matches = re.findall(pattern, text, re.IGNORECASE)

            if matches and len(matches) > 0:
                value = float(matches[0])

                if value or value == 0:
                    return value

        except Exception as e:
            print('ERROR parse_rate_param', e)

    return None
