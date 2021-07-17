# Setup reverse proxy for https with docker-compose and nginx

## docker-compose.yml

```yml
version: "3.3"

services:
  nginx:
    image: tobi312/rpi-nginx:latest
    volumes:
      - ./sites-enabled:/etc/nginx/sites-enabled
      - ./ssl:/etc/ssl/
    ports:
      - 443:443
    network_mode: host
```

## Create self-signed ssl certificate

```shell
mkdir ssl
openssl ecparam -name prime256v1 -genkey -out "ssl/root.key"
openssl req -new -x509 -nodes -sha256 -keyout "root.key" -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -subj "/CN=HOSTNAME" -out "root.crt"
```

## Create default site

```nginx
# /etc/nginx/sites-enabled/default

server {
  listen 443 ssl default_server;
  listen [::]:443 ssl default_server;

  ssl_certificate /etc/ssl/root.crt;
  ssl_certificate_key /etc/ssl/root.key;

  root /var/www/html;
  server_name _;

  location / {
    proxy_pass http://localhost:5000;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    add_header Front-End-Https on;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for ;
  }
}
```

## Run

```shell
sudo docker-compose up
```
