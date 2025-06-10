import http.client
import json
from lib import cache, logger, types_util

@cache.ttl_cache(ttl=3600 * 24 * 30, is_skip_empty=True)
def generate(prompt: str) -> types_util.LocalLlmResponse or None:
    try:
        conn = http.client.HTTPConnection(host='local_llm', port=8090, timeout=60 * 30)

        # Отправим POST-запрос по пути /predict
        conn.request(
            method='POST',
            url='/generate',
            body=json.dumps({'prompt': prompt}),
            headers={'Content-Type': 'application/json'}
        )

        response = conn.getresponse()

        if response.status == 200:
            data = response.read()
            parsed = json.loads(data.decode('utf-8'))

            if 'response' in parsed and parsed['response']:
                return types_util.LocalLlmResponse(
                    prompt=parsed['prompt'],
                    response=parsed['response'],
                    model_name=parsed['model_name'],
                    pretrain_name=parsed['pretrain_name'],
                )

    except Exception as e:
        logger.log_error(method_name='local_llm.generate', error=e, debug_info=f'PROMPT: {prompt}', is_telegram_send=False)

    return None
