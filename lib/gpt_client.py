import requests
from lib import logger

def generate_text(prompt: str, max_new_tokens: int = 200) -> str:
    response = requests.post(
        'http://gpt:8080/generate',
        json={
            'inputs': prompt,
            'parameters': {'max_new_tokens': max_new_tokens}
        }
    )
    response.raise_for_status()
    return response.json()['generated_text']

def generate_llama_cpp(prompt: str, max_tokens: int=128):
    response = requests.post(
        'http://gpt:9090/completion',
        json={
            'prompt': prompt,
            'n_predict': max_tokens,
            'temperature': 0.7,
            'stop': ['</s>']
        }
    )
    response.raise_for_status()
    return response.json()['content']


@logger.error_logger
def try_request(request: str):
    print('GPT REQUEST', request)
    response = generate_llama_cpp(prompt=request)
    print('GPT RESPONSE', response)
