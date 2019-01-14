FROM nginx:latest
RUN apt-get update && apt-get install -y vim openssl wget curl
COPY ./nginx-ultimate-bad-bot-blocker/ /root/
COPY ./ssl.conf /etc/nginx/ssl.conf
COPY ./dhparam.pem /etc/nginx/dhparam.pem
RUN mkdir -p /etc/nginx/sites-available && mkdir -p /etc/nginx/sites-enabled
COPY ./nginx.conf.tpl /etc/nginx/conf.d/default.conf.tpl
RUN ln -s /etc/nginx/sites-available/default.conf /etc/nginx/sites-enabled/default.conf
CMD /bin/bash -c  "envsubst '\$HOST_NAME \$APP_PORT' < /etc/nginx/conf.d/default.conf.tpl > /etc/nginx/conf.d/default.conf && nginx -t && nginx -g 'daemon off;'"
