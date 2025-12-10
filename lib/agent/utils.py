import math
import re
from langchain_core.runnables.graph import MermaidDrawMethod
from io import BytesIO
from PIL import Image
from lib import serializer, db_2, agent, logger
from rich import print_json


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
    if 70 < buy_rate <= 90:
        return lerp(buy_rate, 70, 90, 0.05, 0.2)
    elif 90 < buy_rate <= 100:
        return lerp(buy_rate, 90, 100, 0.2, 0.5)

    return 0


def get_sell_balance_multiply(sell_rate: float) -> float:
    if 0 < sell_rate <= 70:
        return lerp(sell_rate, 0, 70, 0.01, 0.2)
    elif 70 < sell_rate <= 90:
        return lerp(sell_rate, 70, 90, 0.2, 0.5)
    elif 90 < sell_rate <= 100:
        return lerp(sell_rate, 90, 100, 0.5, 1)

    return 0


