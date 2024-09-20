## Deployment Checklist [0.0.1]

* Update/Upgrade
```
sudo apt-get update -y
sudo apt-get upgrade -y
```
* System Dependencies [Nginx, Postgres, Redis-Cache, Image Manipulation]
```
sudo apt install -y nginx
sudo apt-get install postgresql postgresql-contrib -y
sudo apt install redis-server -y

# sudo apt-get install libfreetype6-dev
sudo apt-get install libjpeg-dev zlib1g-dev -y
```

* Python Environment Maintainer, Socket Listener
```
sudo apt install python3-pip -y
sudo apt-get install chaussette -y
```

* Essential Server folders
```
mkdir repo.git app conf logs media static key-files
```

* Begin GIT configuration
```
cd repo.git
git init --bare
git --bare update-server-info
git config core.bare false
git config receive.denycurrentbranch ignore

# Configure Work Tree
git config core.worktree /home/ubuntu/app/
cat > hooks/post-receive <<EOF
#!/bin/sh
git checkout -f
EOF
chmod +x hooks/post-receive
```

* Adding new remote git server

```
Setting up remote git repo on the local
------------------------------------------------------------
git remote add servername user@example.com:/home/ubuntu/repo.git/
git push servername
```

* Python/Build Essentials
```
sudo apt-get install python3.8-dev python3.8-venv -y
sudo apt-get install build-essential libssl-dev libffi-dev python3.8-dev -y
sudo apt install libjpeg8-dev zlib1g-dev

# 7z is used to create a password encrypted database backup (db_backup.py)
sudo apt install p7zip-full

```

* Set up a new virtual environment in server
```
python3.8 -m venv realhrsoft
source realhrsoft/bin/activate
```

* Install dependencies from app folder
```
pip install -r requirements/production.txt
```

* Setup circus [Django/Q-cluster Demonizer] 

```
cd conf/
vim circus.ini
###circus.ini
============================================================
[watcher:webapp]
cmd = daphne --access-log $(circus.env.LOGS_DIR)/access.log  config.asgi:application --fd $(circus.sockets.webapp)
uid=ubuntu
endpoint_owner=rhs
numprocesses = 1
use_sockets = True
copy_env = True
copy_path = True
virtualenv = /home/ubuntu/env/
stdout_stream.class = FileStream
stdout_stream.filename = /home/ubuntu/logs/webapp.log
stderr_stream.class = FileStream
stderr_stream.filename = /home/ubuntu/logs/webapp_err.log
#hooks.after_start = config.hooks.run_raven
# optionally rotate the log file when it reaches 1 gb
# and save 5 copied of rotated files
stdout_stream.max_bytes = 1073741824
stdout_stream.backup_count = 3
stderr_stream.max_bytes = 1073741824
stderr_stream.backup_count = 3
[socket:webapp]
host = 127.0.0.1
port = 8085
[env:webapp]
LOGS_DIR = /home/ubuntu/logs
PYTHONPATH=/home/ubuntu/app/
#NEW_RELIC_CONFIG_FILE=newrelic.ini
[watcher:webapp_q]
cmd = python manage.py qcluster
numprocesses = 1
working_dir = /home/ubuntu/app/
virtualenv = /home/ubuntu/env/
copy_env = True
copy_path = True
stdout_stream.class = FileStream
stdout_stream.filename = /home/ubuntu/logs/webapp_q.log
stderr_stream.class = FileStream
stderr_stream.filename = /home/ubuntu/logs/webapp_q_err.log
[env:webapp_q]
PYTHONPATH=/home/ubuntu/app/
==========================================================
circusd --daemon circus.ini
circusctl reloadconfig
circusctl reload
vim nginx.conf
#nginx.conf
==========================================================
```
* Nginx Configuration [Proxy Pass]
```
==========================================================
# configuration of the server
upstream irhrs-backend {​
    # Nodejs app upstream
    server localhost:8085;
    keepalive 100;
}​
server {​
    # the port your site will be served on
    # the domain name it will serve for
    server_name core.realhrsoft.com; # substitute your machine's IP address or FQDN
    charset     utf-8;
    # max upload size
    client_max_body_size 75M;   # adjust to taste
    root /home/ubuntu/frontend/;
    index index.html index.htm;
    #access_log /home/ubuntu/logs/nginx_access.log;
    #error_log /home/ubuntu/logs/nginx_error.log;
    # Django media
    location /media  {​
        alias /home/ubuntu/media;  # your Django project's media files - amend as required
    }​
    location /static {​
        alias /home/ubuntu/static; # your Django project's static files - amend as required
    }​
    location ~^/((api/v1)|(o[^ffer\-letter]+)|(api/root)|global|permission|api-auth|dj-admin|(a/portal)) {​
        # add_header 'Access-Control-Allow-Origin' '*';
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-NginX-Proxy true;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://irhrs-backend;
    }​
    error_page 404 /error/404/index.html;
    error_page 500 /error/500/index.html;
    location / {​
        try_files $uri $uri/ /index.html ;
    }​
  }​
  server {​
    server_name  domain.realhrsoft.com;
    server_tokens off;
    listen 80;
    return 301 $scheme://domain.realhrsoft.com$request_uri;
}​
==========================================================
```

* Edit nginx configuration

```

; check for issues in nginx configuration
sudo nginx -t


vim /etc/nginx/nginx.conf 
sudo vim /etc/nginx/nginx.conf ##comment the site-enabled and input the new path i.e. /home/ubuntu/conf/nginx.conf
sudo systemctl restart nginx

```

* Configure Database
```
sudo su postgres
createdb exampledb
createuser db_user
psql
\password db_user
GRANT ALL PRIVILEGES ON DATABASE "db" to db_user;
```

* Add postgres dependencies to Django Application
```
cp .env.sample .env
vim .env
```

* Orchestrate Django Configuration

```
# generate public/private keys
./manage.py generate_rsa_keys

# copy app/static files to ~/static directory
./manage.py collectstatic

# create Database schema
./manage.py migrate

# Add admin user to the system, create first organization
./manage.py initial_setup
./manage.py call_seeders
./manage.py seed_org_data
./manage.py seed_organization_commons
./manage.py schedule_tasks
./manage.py seed_id_cards
./manage.py seed_notification_templates
./manage.py setup_hrs_permissions
./manage.py seed_locations

./manage.py seed_initials
./manage.py update_system_admin
```

# General Fixes

* Empty system cache
```
redis-cli flushall
```

* DB configuration for ADMS enabled client [mysql connection]

```
sudo apt install libmysqlclient20 libmysqlclient-dev
```
