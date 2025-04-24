import requests
import time

def query_gpt_local(prompt: str, retries: int = 5) -> str:
    url = 'http://localhost:8080/generate'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'inputs': prompt,
        'parameters': {
            'max_new_tokens': 64,
            'do_sample': False,
        }
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=None)
            response.raise_for_status()
            result = response.json()
            return result['generated_text']  # или result['generated_texts'][0] если API менялось
        except requests.exceptions.RequestException as e:
            print(f'[QueryGPT] Attempt {attempt+1}/{retries} failed: {e}')
            time.sleep(2)

    raise RuntimeError('Failed to get a response from GPT container after several retries.')
