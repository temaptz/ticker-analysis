FROM python:3.12-slim as requirements

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    && apt-get clean

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip
RUN pip install llama-cpp-python[server]


FROM requirements

WORKDIR /app

COPY ./config.json /app/config.json

CMD ["python3", "-m", "llama_cpp.server", "--config_file", "/app/config.json"]
