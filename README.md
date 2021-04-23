# DeckZap
This is the code for game engine and website for DeckZap, a pre-alpha uncollectible card game platform: http://deckzap.com

# Run the app locally for development

I have run the app on a Mac, and the server is Ubuntu Linux.

## Running locally

* Install Python3, Postgres, and virtualenv.
* Make a DB in postgres. Update settings.ini to match whatever values you use for DB name, user, and password

`pip intall -r requirements.txt`
`python manage.py makemigrations`
`python manage.py migrate`
`python manage.py runserver`

# Set up on Digital Ocean

The deckzap.com setup is based on: https://github.com/mitchtabian/HOWTO-django-channels-daphne/blob/master/README.md

I had to tweak the nginx config recommended to get it to work for me:

    upstream channels-backend {
        server 0.0.0.0:8001;
    }

    server {
        server_name 128.199.11.126 deckzap.com www.deckzap.com;

        location = /favicon.ico { access_log off; log_not_found off; }
        location /static/ {
            root /home/django/deckzap/src/deckzap/;
        }

         location / {
            include proxy_params;
            proxy_pass http://unix:/run/gunicorn.sock;
        }

         location /ws {
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_redirect off;
            proxy_pass http://channels-backend;
        }
    }
