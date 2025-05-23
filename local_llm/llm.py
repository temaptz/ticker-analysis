import transformers
import torch
import http.server
import json
import os


def generate(prompt: str) -> str or None:
    try:
        model = transformers.AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=get_model_path(),
            local_files_only=True,
            trust_remote_code=True,
        )
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path=get_model_path(),
            local_files_only=True,
            trust_remote_code=True,
        )

        generator = transformers.pipeline(
            task='text-generation',
            model=model,
            tokenizer=tokenizer,
            device='cpu',
            torch_dtype=torch.float32,
        )

        response = generator(
            prompt,
            max_new_tokens=600,
            temperature=0.6,
            top_p=0.9,
            truncation=False
        )

        if response and len(response) > 0 and response[0] and 'generated_text' in response[0] and response[0]['generated_text']:
            return response[0]['generated_text']

    except Exception as e:
        print('ERROR generate', e)

    return None


def get_model_name() -> str:
    return 'google/gemma-3-4b-it'


def get_models_cache_path() -> str:
    return '/app/models_cache'


def get_model_path() -> str:
    return f'{get_models_cache_path()}/gemma-3-4b-it'


class ServerHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/generate':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''
                body_parsed = json.loads(body.decode('utf-8'))
                prompt = body_parsed.get('prompt')
                generated_text = generate(prompt)

                response = {
                    'prompt': prompt,
                    'response': generated_text,
                    'model_name': get_model_name(),
                    'pretrain_name': None,
                }
                response_bytes = json.dumps(response).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Length', str(len(response_bytes)))
                self.end_headers()
                self.wfile.write(response_bytes)
            except Exception as e:
                print('ERROR do_POST', e)
                self.send_error(500, 'Internal Server Error')
        else:
            self.send_error(404, 'Not Found')


def run_server():
    port = 8090
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, ServerHandler)
    print(f'Server running on port {port}...')
    httpd.serve_forever()

print('MODEL DIR\n', os.listdir(get_model_path()))

run_server()
