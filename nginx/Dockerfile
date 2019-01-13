FROM nginx:latest
RUN apt-get update && apt-get install -y vim openssl
COPY ./ssl.conf /etc/nginx/ssl.conf
COPY ./dhparam.pem /etc/nginx/dhparam.pem
COPY ./nginx.conf.tpl /etc/nginx/conf.d/default.conf.tpl
CMD /bin/bash -c  "envsubst '\$HOST_NAME \$APP_PORT' < /etc/nginx/conf.d/default.conf.tpl > /etc/nginx/conf.d/default.conf && nginx -t && nginx -g 'daemon off;'"
