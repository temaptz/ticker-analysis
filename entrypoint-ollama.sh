#!/usr/bin/env sh
set -eu

# MODEL_NAME обязателен и задаётся через окружение (без дефолтов)
if [ -z "${MODEL_NAME:-}" ]; then
  echo "[entrypoint] ERROR: MODEL_NAME не задан. Установите переменную окружения MODEL_NAME." >&2
  exit 1
fi
MODEL_NAME="$MODEL_NAME"

# Клиентский хост для локального доступа к API внутри контейнера
CLIENT_HOST="${OLLAMA_CLIENT_HOST:-127.0.0.1:11434}"

echo "[entrypoint] Запускаю Ollama сервер..."
ollama serve &
SERVER_PID=$!

cleanup() {
  echo "[entrypoint] Останавливаю Ollama сервер (PID $SERVER_PID)..."
  kill -TERM "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo "[entrypoint] Жду готовности API Ollama на $CLIENT_HOST..."
i=0
until OLLAMA_HOST="$CLIENT_HOST" ollama list >/dev/null 2>&1; do
  i=$((i+1))
  if [ "$i" -gt 120 ]; then
    echo "[entrypoint] API Ollama не стало доступно за разумное время" >&2
    exit 1
  fi
  sleep 1
done

echo "[entrypoint] Проверяю наличие модели: $MODEL_NAME"
if ! OLLAMA_HOST="$CLIENT_HOST" ollama list | grep -Fq "$MODEL_NAME"; then
  echo "[entrypoint] Модель не найдена. Загружаю $MODEL_NAME ..."
  OLLAMA_HOST="$CLIENT_HOST" ollama pull "$MODEL_NAME"
else
  echo "[entrypoint] Модель уже загружена."
fi

echo "[entrypoint] Ollama запущен. Перехожу в foreground..."
wait "$SERVER_PID"


