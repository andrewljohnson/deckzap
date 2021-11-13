# DeckZap
This is the code for game engine and website for DeckZap, a pre-alpha uncollectible card game platform: http://deckzap.com

# Run the app locally for development

I have run the app on a Mac, and the server is Ubuntu Linux.

## Running locally

Copy `.env.example` and add a `SECRET_KEY`. Then run:

`docker-compose up`

## CI

Tests run automatically with GitHub Actions. The Docker images are also built here, and stored in GitHub Packages.
A personal access token is required to push the images to GitHub Packages. The access token ([generated here](https://github.com/settings/tokens))
should be stored in GitHub Repository Secrets as `PERSONAL_ACCESS_TOKEN`.

## CD

The app is deployed automatically to prod from the master branch once tests pass. Production secrets are stored in
GitHub Repository Secrets. The production Docker containers run on a DigitalOcean droplet. The Docker images are
pulled from GitHub packages with the same access token that is used in CI.

# Graphics

Graphics from: https://game-icons.net/

# Working Docs

[Figma Assets](https://www.figma.com/file/eSJ5urEoWnWos8uHb5ZsbG/DeckZap-Assets?node-id=0%3A1)

[ToDo](https://docs.google.com/document/d/1lCRn96Zj2yh1rm-wDA4Z1b90QRmvyh-EUM6z9DSxXT8/edit)
