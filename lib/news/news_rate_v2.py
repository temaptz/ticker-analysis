import re
import datetime

from lib.db_2 import news_db, news_rate_2_db
from lib import instruments, yandex, cache, counter, docker, serializer, utils, logger, types_util, local_llm


@logger.error_logger
def get_news_rate_db(
        news_uid: str,
        instrument_uid: str,
) -> types_util.NewsRate2 or None:
    rate = news_rate_2_db.get_rate(instrument_uid=instrument_uid, news_uid=news_uid) or []

    if len(rate) > 0:
        last_rate = rate[0]
        result = types_util.NewsRate2(
            sentiment=last_rate.sentiment,
            impact_strength=last_rate.impact_strength,
            mention_focus=last_rate.mention_focus,
            model_name=last_rate.model_name,
            pretrain_name=last_rate.pretrain_name,
            generation_time_sec=last_rate.generation_time_sec,
            generation_date=last_rate.generation_date,
        )

        if result.is_ready_to_calc():
            result.get_influence_score_value()
            return result

    return None

@logger.error_logger
def get_news_total_influence_score(
        instrument_uid: str,
        news_ids: list[str],
) -> float or None:
    rates: list[types_util.NewsRate2] = list()

    for n_id in news_ids:
        if rate := get_news_rate_db(instrument_uid=instrument_uid, news_uid=n_id):
            rates.append(rate)

    if len(rates) > 0:
        result = 0

        for r in rates:
            if r.is_ready_to_calc():
                result += r.get_influence_score_value()

        return result

    return None


@logger.error_logger
def get_news_rate(
        news_uid: str,
        instrument_uid: str,
) -> types_util.NewsRate2 or None:
    if news := news_db.get_news_by_uid(news_uid=news_uid):
        if instrument := instruments.get_instrument_by_uid(uid=instrument_uid):
            if subject_name := instruments.get_instrument_human_name(uid=instrument.uid):
                rate = get_text_rate(
                    text=utils.clean_news_text_for_llm(title=news.title, text=news.text),
                    subject_name=subject_name,
                )

                if rate and rate.is_ready_to_calc():
                    return rate

    return None


@logger.error_logger
def get_text_rate(text: str, subject_name: str) -> types_util.NewsRate2 or None:
    # print('------------------------------------------------------------------')
    # print('GPT REQUEST\n', get_prompt(news_text=text, subject_name=subject_name))

    resp: types_util.LocalLlmResponse or None = local_llm.generate(
        prompt=get_prompt(news_text=text, subject_name=subject_name)
    )

    if resp:
        sentiment = parse_rate_param(text=resp.response, param_name='sentiment')
        impact_strength = parse_rate_param(text=resp.response, param_name='impact_strength')
        mention_focus = parse_rate_param(text=resp.response, param_name='mention_focus')

        # print('GPT RESPONSE\n', resp)
        # print('------------------------------------------------------------------')
        # print('GPT PARAM PARSED sentiment', sentiment)
        # print('GPT PARAM PARSED impact_strength', impact_strength)
        # print('GPT PARAM PARSED mention_focus', mention_focus)
        # print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')

        rate = types_util.NewsRate2(
            sentiment=sentiment,
            impact_strength=impact_strength,
            mention_focus=mention_focus,
            llm_response=resp,
        )

        if rate and rate.is_ready_to_calc():
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

def get_response(sentiment: float, impact_strength: float, mention_focus: float) -> str:
    return f'''sentiment: {sentiment}\nimpact_strength: {impact_strength}\nmention_focus: {mention_focus}'''


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
