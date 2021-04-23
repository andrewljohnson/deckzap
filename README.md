# deckzap
Demo games for a board and card game platform.

http://deckzap.com

# Run the app locally for development

I have run the app on a Mac, and the server is Ubuntu Linux.

## Running locally

* Install Python3, Postgres, and virtualenv.
* Make a postgres database. Update settings.ini
* `pip intall -r requirements.txt`
* `python manage.py runserver`

# Set up on Digital Ocean

The deckzap.com setup is based on: https://github.com/mitchtabian/HOWTO-django-channels-daphne/blob/master/README.md

 * had to tweak the nginx config provided to get it to work

## Create Digital Ocean Droplet with SSH login

You need a Digital Ocean account:

* create a new droplet
 * Ubuntu 20.04
 * SF Region
 * use SSH keys for auth
 * enable backups

Write down your server ip somewhere. You'll need this for logging into your server.

## SSH to the Server

`ssh -i PATH_TO_KEY root@IP_YOU_COPIED_EARLIER`
