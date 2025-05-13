from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
import os
import sys
sys.stdout.reconfigure(line_buffering=True)


def tokenize_function(record):
    prompt = f'''
Ты — финансовый аналитик. Оцени следующую новость относительно её влияния на стоимость акций компании {record['subject_name']}.

Заполни три признака:

1. sentiment — тон новости относительно компании (от -1.0 до +1.0)
2. impact_strength — сила потенциального влияния на цену акций (от 0.0 до 1.0)
3. mention_focus — насколько явно и подробно упоминается компания (от 0.0 — вскользь до 1.0 — явно и подробно)

Ответ в формате:
sentiment: [значение]
impact_strength: [значение]
mention_focus: [значение]

Текст новости:
{record['news_text']}
'''

    answer = f'''sentiment: {record['sentiment']}
impact_strength: {record['impact_strength']}
mention_focus: {record['mention_focus']}'''

    full_text = prompt.strip() + '\n\n' + answer.strip()

    tokenized = tokenizer(
        full_text,
        truncation=True,
        padding='max_length',
        max_length=1024,
        return_tensors=None  # обязательно!
    )

    tokenized['labels'] = tokenized['input_ids'].copy()

    # 🔥 Вернуть только нужные ключи!
    return {
        'input_ids': tokenized['input_ids'],
        'attention_mask': tokenized['attention_mask'],
        'labels': tokenized['labels']
    }




print('START FINETUNE')

# Путь к модели safetensors
MODEL_PATH = '/models/llama-3-8b-gpt-4o-ru1.0'  # Монтируйте в docker-compose как volume

print('MODEL PATH IS DIR', os.path.isdir(MODEL_PATH), MODEL_PATH)


# Загрузка модели и токенизатора
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
    local_files_only=True,
)
print('MODEL LOADED')
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
    local_files_only=True,
)
print('TOKENIZER LOADED')

# Загрузка датасета CSV
print('\n[INFO] Загрузка датасета...', flush=True)
dataset = load_dataset('csv', data_files={'train': '/models/datasets/news_500.csv'}, delimiter=',')

print('DATASET LOADED', dataset)

# Настройка LoRA
print('\n[INFO] Настройка LoRA...', flush=True)
lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=['q_proj', 'v_proj'],
    lora_dropout=0.05,
    bias='none',
    task_type='CAUSAL_LM'
)
model = get_peft_model(model, lora_config)

# Аргументы обучения
training_args = TrainingArguments(
    output_dir='/finetuned',  # Монтировать как volume в docker-compose
    overwrite_output_dir=True,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=16,
    save_steps=100,
    save_total_limit=2,
    logging_steps=20,
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_steps=100,
    logging_dir='/finetuned/logs',
    bf16=False,  # CPU
    fp16=False,
    report_to='none',
    remove_unused_columns=False,
)

# Data collator для masked language modeling
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

tokenized_dataset = dataset['train'].map(
    tokenize_function,
    batched=False,
    remove_columns=dataset['train'].column_names  # ❗ убираем все поля кроме input_ids/labels
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

# Старт обучения
print('\n[INFO] Начало обучения...', flush=True)
trainer.train()

# Сохраняем LoRA адаптеры
print('\n[INFO] Сохраняем модель...', flush=True)
model.save_pretrained('/finetuned')
tokenizer.save_pretrained('/finetuned')

print('\n[INFO] Обучение завершено.', flush=True)
