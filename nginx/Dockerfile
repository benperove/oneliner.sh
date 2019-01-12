FROM nginx:latest
RUN apt-get update && apt-get install -y vim
COPY ./nginx.conf.tpl /etc/nginx/conf.d/default.conf.tpl
CMD /bin/bash -c  "envsubst '\$HOST_NAME \$APP_PORT' < /etc/nginx/conf.d/default.conf.tpl > /etc/nginx/conf.d/default.conf && nginx -t && nginx -g 'daemon off;'"

#tail -f /var/log/nginx/access.log
#nginx -g 'daemon off;
