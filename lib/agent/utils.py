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
