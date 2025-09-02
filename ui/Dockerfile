# Установка зависимостей
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json .
RUN npm install --force


# Сборка проекта
FROM node:20-slim AS build
ENV NG_BUILD_MAX_WORKERS=1
ENV NG_BUILD_PARALLEL_TS=0
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

§
# Nginx
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем файл с пользователями
COPY htpasswd /etc/nginx/.htpasswd

# Копируем билд ангуляра
COPY --from=build /app/dist/ui /usr/share/nginx/html

# Директория для сертификатов (смонтируется в compose)
RUN mkdir -p /etc/nginx/certs
