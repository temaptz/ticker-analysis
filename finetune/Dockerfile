FROM python:3.12-slim as requirements

# Установка зависимостей
#RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка Python-библиотек
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM requirements

# Копируем скрипты обучения
COPY ./finetune.py /app/finetune.py

CMD ["python", "finetune.py"]