FROM nginx:alpine

WORKDIR /app

COPY ./dist . 

COPY nginx.conf /etc/nginx/conf.d/

EXPOSE 80


