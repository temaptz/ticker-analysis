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

CMD ["python3", "-m", "llama_cpp.server", "--model", "/models/DeepHermes-3-Llama-3-8B-F16.gguf"]
