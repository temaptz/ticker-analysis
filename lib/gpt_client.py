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

@logger.error_logger
def try_request(request: str):
    print('GPT REQUEST', request)
    response = generate_text(request)
    print('GPT RESPONSE', response)
