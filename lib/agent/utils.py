import datetime
import math
import re
from langchain_core.runnables.graph import MermaidDrawMethod
from io import BytesIO
from PIL import Image
from lib import serializer, db_2, agent, logger, instruments, utils, tech_analysis
from rich import print_json
from t_tech.invest import CandleInterval
from t_tech.invest.schemas import IndicatorType


def draw_graph(graph):
    try:
        png_bytes = graph.get_graph(
            xray=True
        ).draw_mermaid_png(
            draw_method=MermaidDrawMethod.PYPPETEER
        )
        img = Image.open(BytesIO(png_bytes))
        img.show()

    except Exception as e:
        print('ERROR', e)
        pass

def output_json(obj):
    print_json(serializer.to_json(obj))


def get_last_message_content(state: agent.models.State) -> str or None:
    if messages := state.get('messages', []):
        if len(messages) > 0 and messages[-1] and messages[-1].content:
            return messages[-1].content
    return None

def get_buy_rate(instrument_uid: str) -> int or None:
    if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument_uid, tag_name='llm_buy_rate'):
        if tag.tag_value:
            return int(tag.tag_value)
    return None

def get_buy_conclusion(instrument_uid: str) -> int or None:
    if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument_uid, tag_name='llm_buy_conclusion'):
        if tag.tag_value:
            return tag.tag_value
    return None

def get_sell_rate(instrument_uid: str) -> int or None:
    if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument_uid, tag_name='llm_sell_rate'):
        if tag.tag_value:
            return int(tag.tag_value)
    return None

def get_sell_conclusion(instrument_uid: str) -> int or None:
    if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument_uid, tag_name='llm_sell_conclusion'):
        if tag.tag_value:
            return tag.tag_value
    return None


def trim_prompt(prompt: str) -> str:
    try:
        s = prompt.replace('\\n', ' ').replace('\r\n', ' ').replace('\n', ' ')
        # сжать любые повторяющиеся пробельные символы в один пробел
        s = re.sub(r'\s+', ' ', s)
        return s.strip()
    except Exception as e:
        logger.log_error(method_name='trim_prompt', error=e)
    return ''


# DEPRECATED
def lerp(x: float, a: float, b: float, y0: float, y1: float) -> float:
    """
    Линейная интерполяция.
    Возвращает значение, соответствующее позиции x на отрезке [a, b],
    интерполированное в отрезок [y0, y1].
    Если b == a возвращает y0 (защита от деления на ноль).
    Замечание: сама по себе функция не обрезает результат при x вне [a,b].
    """
    return y0 + (0 if b == a else (x - a) / (b - a)) * (y1 - y0)


def linear_interpolation(x: float, a: float, b: float, y0: float, y1: float) -> float:
    """
    Простая и надёжная линейная интерполяция.
    Корректно работает при любом порядке a и b (включая отрицательные значения).
    Возвращает значение, соответствующее позиции x на отрезке [a, b] в шкале [y0, y1].
    Если a и b практически равны — возвращает y0 (защита от деления на ноль).
    Результат не обрезается, если x вне [a, b].
    """
    x = float(x); a = float(a); b = float(b); y0 = float(y0); y1 = float(y1)
    if math.isclose(a, b):
        return y0
    t = (x - a) / abs(b - a)
    return y0 + t * (y1 - y0)


def get_buy_balance_multiply(buy_rate: float) -> float:
    if 0.7 <= buy_rate <= 0.9:
        return linear_interpolation(buy_rate, 0.7, 0.9, 0.1, 0.5)
    elif 0.9 < buy_rate <= 1:
        return 0.5

    return 0


def get_sell_balance_multiply(sell_rate: float) -> float:
    if 0.7 <= sell_rate <= 0.9:
        return linear_interpolation(sell_rate, 0.7, 0.9, 0.5, 1)
    elif 0.9 < sell_rate <= 1:
        return 1

    return 0


def get_buy_price(instrument_uid: str, l_level: int = 1) -> float | None:
    if last_price := _get_last_price(instrument_uid=instrument_uid):
        if support_resistance := _get_support_resistance(instrument_uid=instrument_uid):
            if k := _get_gold_k(support_resistance=support_resistance, l_level=l_level):
                price = min(support_resistance) + k
                max_price = last_price * 0.9975
                if price < max_price:
                    return price
                else:
                    return max_price
    return None


def get_sell_price(instrument_uid: str, l_level: int = 1) -> float | None:
    if last_price := _get_last_price(instrument_uid=instrument_uid):
        if support_resistance := _get_support_resistance(instrument_uid=instrument_uid):
            if k := _get_gold_k(support_resistance=support_resistance, l_level=l_level):
                price = max(support_resistance) - k
                min_price = last_price * 1.0025
                if price > min_price:
                    return price
                else:
                    return min_price
    return None


# Расчет коэфициента матожиданя цены сделки методом золотого сечения
def _get_gold_k(support_resistance: (float, float), l_level: int = 1) -> float:
    return abs(support_resistance[1] - support_resistance[0]) / (2.618 ** l_level)


# Минимумы максимумы цены за последнее время
def _get_support_resistance(instrument_uid: str) -> (float, float) or None:
    candles_count = 48
    if (candles := instruments.get_instrument_history_price_by_uid(
        uid=instrument_uid,
        days_count=10,
        interval=CandleInterval.CANDLE_INTERVAL_HOUR,
        to_date=datetime.datetime.now()
    )) and len(candles) >= candles_count:
        lastest_candles = sorted(candles, key=lambda i: i.time)[candles_count:]
        prices_high = [utils.get_price_by_quotation(i.close) for i in lastest_candles]
        prices_low = [utils.get_price_by_quotation(i.close) for i in lastest_candles]
        highest = max(prices_high)
        lowest = min(prices_low)

        if highest and lowest:
            return lowest, highest

    return None

def _get_last_price(instrument_uid: str) -> float | None:
    return instruments.get_instrument_last_price_by_uid(uid=instrument_uid)
