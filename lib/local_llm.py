import requests
from lib import logger, serializer, docker

@logger.error_logger
def query_gpt_local(prompt: str) -> str or None:
    url = 'http://gpt:8080/v1/completions' if docker.is_docker() else 'http://localhost:8080/v1/completions'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'prompt': prompt,
        'model': 'llama-3-8b'
    }

    response = requests.post(url, headers=headers, json=payload, timeout=None)

    if response:
        result = response.json()

        if result and result['choices'] and result['choices'][0] and result['choices'][0]['text']:
            logger.log_info(message='GPT RESPONSE USAGE', output=serializer.to_json(result['usage']))

            return result['choices'][0]['text']

    return None
