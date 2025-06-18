from langchain_core.runnables.graph import MermaidDrawMethod
from io import BytesIO
from PIL import Image


def draw_graph(graph):
    try:
        png_bytes = graph.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.PYPPETEER
        )
        img = Image.open(BytesIO(png_bytes))
        img.show()

    except Exception as e:
        print('ERROR', e)
        pass