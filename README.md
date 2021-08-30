# DeckZap
This is the code for game engine and website for DeckZap, a pre-alpha uncollectible card game platform: http://deckzap.com

# Run the app locally for development

I have run the app on a Mac, and the server is Ubuntu Linux.

## Running locally

* Install Python3, Postgres, virtualenv, parcel, and yarn.
* Make a DB in postgres. Update settings.ini to match whatever values you use for DB name, user, and password

`yarn install`

`pip install -r requirements.txt`

`python manage.py makemigrations`

`python manage.py migrate`

`python manage.py runserver`

# Set up on Digital Ocean

The deckzap.com setup is based on this repo: [HOWTO-django-channels-daphne](https://github.com/mitchtabian/HOWTO-django-channels-daphne/blob/master/README.md)

I had to change the nginx config recommended to this code to get it to work for me:

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

# Graphics

Graphics from: https://game-icons.net/

# Working Docs

[Latest card ideas](https://docs.google.com/spreadsheets/d/1QwQofwkO4v2PjAuxQv9dMr1k491FDIUTkObtUcRrdBE/edit#gid=0)

[Figma Assets](https://www.figma.com/file/eSJ5urEoWnWos8uHb5ZsbG/DeckZap-Assets?node-id=0%3A1)

[ToDo](https://docs.google.com/document/d/1XD804l5Vr6fjHL8jLJNQEK_Lt83r0QRgQe9mmT93BJ0/edit?usp=sharing)