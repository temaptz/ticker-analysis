import transformers
import torch
import http.server
import json
import os
import peft
import pandas
import datasets
import math


GENERATOR: transformers.Pipeline or None = None

def generate(prompt: str) -> str or None:
    try:
        if GENERATOR:
            print('-----------------START GENERATE RESPONSE-----------------')
            response = GENERATOR(
                prompt,
                max_new_tokens=600,
                temperature=0.6,
                top_p=0.9,
                truncation=False
            )

            if response and len(response) > 0 and response[0] and 'generated_text' in response[0] and response[0]['generated_text']:
                print('RESPONSE:\n', response[0]['generated_text'])
                return response[0]['generated_text']
            else:
                print('EMPTY RESPONSE\n', response)

            print('^^^^^^^^^^^^^^^^^^END GENERATE RESPONSE^^^^^^^^^^^^^^^^^^')

        else:
            print('GENERATOR IS NOT INITIALIZED')

    except Exception as e:
        print('ERROR generate', e)

    return None


def init_generator() -> transformers.Pipeline or None:
    try:
        model = transformers.AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=get_model_path(),
            local_files_only=True,
            trust_remote_code=True,
        )
        model = peft.PeftModel.from_pretrained(model, get_adapter_path())
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path=get_adapter_path(),
            local_files_only=True,
            trust_remote_code=True,
        )

        return transformers.pipeline(
            task='text-generation',
            model=model,
            tokenizer=tokenizer,
            device='cpu',
            torch_dtype=torch.float32,
        )
    except Exception as e:
        print('ERROR init_generator', e)

    return None


def compute_metrics(eval_preds):
    if isinstance(eval_preds, tuple):
        loss = eval_preds[0]
    elif isinstance(eval_preds, dict) and 'loss' in eval_preds:
        loss = eval_preds['loss']
    else:
        return {}

    if isinstance(loss, (list, np.ndarray)):
        loss = np.mean(loss)
    elif hasattr(loss, 'item'):
        loss = loss.item()

    perplexity = math.exp(loss) if loss < 50 else float('inf')
    return {'perplexity': perplexity}


def train():
    df = pandas.read_csv(f'{get_app_dir()}/dataset.csv')

    # Формируем строки для обучения в формате диалога
    samples = [{'text': f'User: {row.prompt.strip()} \nAssistant: {row.response.strip()}'} for _, row in df.iterrows()]

    # Превращаем в HuggingFace Dataset
    dataset = datasets.Dataset.from_list(samples)

    ds_split = dataset.train_test_split(test_size=0.1, seed=42)
    train_ds, val_ds = ds_split['train'], ds_split['test']

    tokenizer = transformers.AutoTokenizer.from_pretrained(
        pretrained_model_name_or_path=get_model_path(),
        local_files_only=True,
        trust_remote_code=True,
    )

    def preprocess(example):
        return tokenizer(example['text'], truncation=True, max_length=512)

    tokenized_train = train_ds.map(preprocess, batched=False)
    tokenized_val = val_ds.map(preprocess, batched=False)

    print('\n========== TOKENIZED TRAIN DATASET ==========')
    print(tokenized_train)
    print('\n----- First 10 entries (tokenized) -----')
    for i, sample in enumerate(tokenized_train.select(range(10))):
        print(f'\nExample #{i + 1}')
        print(sample)

    print('\n========== TOKENIZED VALIDATION DATASET ==========')
    print(tokenized_val)
    print('\n----- First 10 entries (tokenized) -----')
    for i, sample in enumerate(tokenized_val.select(range(10))):
        print(f'\nExample #{i + 1}')
        print(sample)

    lora_config = peft.LoraConfig(
        task_type=peft.TaskType.CAUSAL_LM,
        r=8,               # Размер LoRA-адаптера (чем больше — тем "мощнее" адаптер, но и дольше обучается)
        lora_alpha=16,     # Масштаб градиентов (обычно 16 или 32)
        lora_dropout=0.05, # Вероятность отключения некоторых связей во время обучения, чтобы избежать переобучения
        target_modules=[
            'q_proj',
            'k_proj',
            'v_proj',
            'o_proj',
        ],
    )

    # === 4. Загрузка модели и подключение LoRA ===
    model = transformers.AutoModelForCausalLM.from_pretrained(
        pretrained_model_name_or_path=get_model_path(),
        local_files_only=True,
        trust_remote_code=True,
    )
    model.gradient_checkpointing_enable()  # экономим RAM
    model = peft.get_peft_model(model, lora_config)

    # === 5. Параметры тренировки ===
    training_args = transformers.TrainingArguments(
        output_dir=get_adapter_path(),       # Куда сохранять LoRA-адаптер
        num_train_epochs=5,                  # Сколько раз пройти по датасету (обычно 2-5)
        per_device_train_batch_size=1,       # Размер батча (для CPU обычно 1)
        per_device_eval_batch_size=1,
        learning_rate=2e-4,                  # Скорость обучения (можно уменьшить при переобучении)
        logging_steps=5,                     # Как часто писать логи
        eval_strategy='steps',               # запускаем eval каждые N шагов
        eval_steps=100,
        save_strategy='steps',
        save_steps=100,                      # Как часто сохранять чекпоинты
        load_best_model_at_end=True,         # в конце вернёт лучшую по метрике версию
        metric_for_best_model='eval_loss',
        greater_is_better=False,
        save_total_limit=5,                  # Сколько последних чекпоинтов хранить
        use_cpu=True,
    )

    # === 6. Trainer и запуск ===
    trainer = transformers.Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
        compute_metrics=compute_metrics,
        callbacks=[transformers.EarlyStoppingCallback(early_stopping_patience=3)]
    )

    trainer.train(resume_from_checkpoint=is_adapter_exists())

    # === 7. Сохраняем адаптер и токенизатор ===
    model.save_pretrained(get_adapter_path())
    tokenizer.save_pretrained(get_adapter_path())


def get_model_name() -> str:
    return 'google/gemma-3-4b-it'


def get_pretrain_name() -> str:
    return 'dataset-500_v0'


def get_app_dir() -> str:
    if os.path.exists('/app'):
        return '/app'

    return os.path.abspath('./')


def get_models_cache_path() -> str:
    return f'{get_app_dir()}/models_cache'


def get_model_path() -> str:
    return f'{get_models_cache_path()}/gemma-3-4b-it'


def get_adapter_path() -> str:
    return f'{get_models_cache_path()}/lora_adapter'


def is_adapter_exists() -> bool:
    return os.path.exists(get_adapter_path()) and len(os.listdir(get_adapter_path())) > 0


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
                    'pretrain_name': get_pretrain_name(),
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

if not is_adapter_exists():
    os.makedirs(get_adapter_path(), exist_ok=True)
print('MODEL DIR\n', os.listdir(get_model_path()))
print('ADAPTER DIR\n', os.listdir(get_adapter_path()))

if not os.listdir(get_adapter_path()):
    print('START TRAIN ADAPTER')
    train()
    print('END TRAIN ADAPTER')

GENERATOR = init_generator()

run_server()
