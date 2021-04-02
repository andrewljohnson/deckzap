# demogames
Demo games for a board and card game platform.

# Set up on Digital Ocean

Based on: https://github.com/mitchtabian/HOWTO-django-channels-daphne/blob/master/README.md

## Create Digital Ocean Droplet with SSH login

You need a Digital Ocean account:

* create a new droplet
 * Ubuntu 20.04
 * SF Region
 * use SSH keys for auth
 * enable backups

Write down your server ip somewhere. You'll need this for logging into your server.

## SSH to the Server

ssh -i PATH_TO_KEY root@IP_YOU_COPIED_EARLIER

## Install Server Dependencies
Run these commands in the SSH terminal.

`passwd` Set password for root.

`sudo apt update`

`sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl`

`sudo -u postgres psql`

`CREATE DATABASE django_db;`

`CREATE USER django WITH PASSWORD 'password';`

`ALTER ROLE django SET client_encoding TO 'utf8';`

`ALTER ROLE django SET default_transaction_isolation TO 'read committed';`

`ALTER ROLE django SET timezone TO 'UTC';`

`GRANT ALL PRIVILEGES ON DATABASE django_db TO django;`

`\q`

`sudo -H pip3 install --upgrade pip`

`sudo -H pip3 install virtualenv`

`sudo apt install git-all`

`sudo apt install libgl1-mesa-glx` Resolve cv2 issue

`adduser django`

`su django`

`cd /home/django/`

`mkdir CodingWithMitchChat` You can replace "CodingWithMitchChat" with your project name. 

`cd CodingWithMitchChat`

`virtualenv venv`

`source venv/bin/activate`

`mkdir src`


#### settings.py
Top of the file:
```python
from pathlib import Path
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ["<ip_from_digital_ocean>",]
ROOT_URLCONF = f'{config("PROJECT_NAME")}.urls'
WSGI_APPLICATION = f'{config("PROJECT_NAME")}.wsgi.application'
ASGI_APPLICATION = f'{config("PROJECT_NAME")}.routing.application'

```

Bottom of the file:
after it works put settings.py code here

```python

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config("DB_NAME"),
        'USER': config("DB_USER"),
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': 'localhost',
        'PORT': '',
    }
}

```

#### manage.py
Update this to use config.

```
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from decouple import config


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{config("PROJECT_NAME")}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```
