server {
	listen 80;
	listen [::]:80;
    server_name ${HOST_NAME};

	location ^~ /(login|oauth2|me) {
		return 301 https://$host$request_uri;
	}

	location / {
	   proxy_set_header Host $host;
	   proxy_set_header X-Real-IP $remote_addr;
	   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	   proxy_set_header X-Forwarded-Proto $scheme;
	   proxy_pass http://oneliner:$APP_PORT;  
	}

}

server {
 listen 443 ssl http2;
 listen [::]:443 ssl http2;
 
 # SSL config
 ssl on;
 ssl_certificate /etc/letsencrypt/live/${HOST_NAME}/fullchain.pem;
 ssl_certificate_key /etc/letsencrypt/live/${HOST_NAME}/privkey.pem;

 
 location / {
   
    # HTTP 1.1 support

    proxy_http_version 1.1;
    proxy_set_header Connection "";

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_pass http://oneliner:$APP_PORT;
    
    proxy_buffering off;
    client_max_body_size 0;
    proxy_read_timeout 36000s;
    proxy_redirect off;
    proxy_ssl_session_reuse off;
 }
}
