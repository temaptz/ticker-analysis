FROM node:18-alpine AS build
WORKDIR /usr/src/app
COPY * ./
RUN npm install --force
COPY . .
RUN npm run build


FROM nginx:stable-alpine
# Копируем конфиг nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем файл с пользователями
COPY htpasswd /etc/nginx/.htpasswd

# Копируем билд ангуляра
COPY --from=build /usr/src/app/dist/ui/browser /usr/share/nginx/html
