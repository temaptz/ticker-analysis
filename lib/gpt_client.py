import requests
from llama_cpp import Llama
from lib import logger, cache

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

llm = Llama(
    model_path='/app/llm_models/DeepHermes-3-Llama-3-8B-F16.gguf',
    n_ctx=4096,
    n_threads=4,
    verbose=True
)

@cache.ttl_cache(ttl=3600 * 24 * 30)
def generate_text_llama(request: str) -> str or None:
    try:
        resp = llm(request, max_tokens=150)
        text_response = resp['choices'][0]['text']

        if text_response:
            return text_response
    except Exception as e:
        logger.log_error(method_name='generate_text_llama', error=e)

    return None

