import http.client
import json
from lib import cache, logger, types

@cache.ttl_cache(ttl=3600 * 24 * 30, skip_empty=True)
@logger.error_logger
def generate(prompt: str) -> types.LocalLlmResponse or None:
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
            return types.LocalLlmResponse(
                prompt=parsed['prompt'],
                response=parsed['response'],
                model_name=parsed['model_name'],
                pretrain_name=parsed['pretrain_name'],
            )

    return None
