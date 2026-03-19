FROM node:20-slim AS deps

WORKDIR /app

COPY package.json .

RUN npm install --force


FROM node:20-slim AS build

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG AUTHENTIK_JWT_ISSUER
ARG AUTHENTIK_CLIENT_ID
ENV AUTHENTIK_JWT_ISSUER=${AUTHENTIK_JWT_ISSUER}
ENV AUTHENTIK_CLIENT_ID=${AUTHENTIK_CLIENT_ID}

RUN sed -i "s|{AUTHENTIK_JWT_ISSUER}|$AUTHENTIK_JWT_ISSUER|g" /app/src/app/auth.config.ts
RUN sed -i "s|{AUTHENTIK_CLIENT_ID}|$AUTHENTIK_CLIENT_ID|g" /app/src/app/auth.config.ts

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY htpasswd /etc/nginx/.htpasswd
COPY --from=build /app/dist/ui /usr/share/nginx/html
COPY --from=build /app/src /app_src

