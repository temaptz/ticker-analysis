FROM node:23-alpine AS build
WORKDIR /usr/src/app
COPY * ./
RUN npm install
COPY . .
RUN npm run build


FROM nginx:alpine
COPY --from=build /usr/src/app/dist/ui/browser /usr/share/nginx/html
