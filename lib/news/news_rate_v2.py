import datetime

from django.db.models.expressions import result

import const
from lib.db_2 import news_db
from lib import instruments, yandex, cache, counter, docker, serializer, utils, logger, types, local_llm


def get_news_rate(
        news_uid: [str],
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

    return None


def get_text_rate(text: str, subject_name: str) -> types.NewsRate2 or None:
    resp = local_llm.query_gpt_local(
        prompt=get_prompt(news_text=text, subject_name=subject_name)
    )

    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('GPT REQUEST\n', get_prompt(news_text=text, subject_name=subject_name))
    print('GPT RESPONSE\n', resp)
    print('GPT PARAM PARSED sentiment\n', parse_rate_param(resp=resp, param_name='sentiment'))
    print('GPT PARAM PARSED impact_strength\n', parse_rate_param(resp=resp, param_name='impact_strength'))
    print('GPT PARAM PARSED mention_focus\n', parse_rate_param(resp=resp, param_name='mention_focus'))
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')

    return None


def get_prompt(subject_name: str, news_text: str) -> str:
    return f'''
Ты — финансовый аналитик. Оцени следующую новость относительно её влияния на стоимость акций компании {subject_name}.

Заполни три признака:

1. sentiment — тон новости относительно компании (от -1.0 до +1.0)
2. impact_strength — сила потенциального влияния на цену акций (от 0.0 до 1.0)
3. mention_focus — насколько явно и подробно упоминается компания (от 0.0 — вскользь до 1.0 — явно и подробно)

Ответ в формате:
sentiment: [значение]
impact_strength: [значение]
mention_focus: [значение]

Текст новости:
{news_text}
'''


def parse_rate_param(resp: str, param_name: str) -> float or None:
    if resp:
        lines = resp.split('\n')
        for line in lines:
            if param_name in line:
                try:
                    value = float(line.split(':')[1].strip())
                    return value
                except (IndexError, ValueError):
                    return None
    return None
