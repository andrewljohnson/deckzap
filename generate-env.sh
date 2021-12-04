#!/bin/bash
echo DEBUG=$DEBUG >> .env
echo PROJECT_NAME=$PROJECT_NAME >> .env
echo SECRET_KEY=$SECRET_KEY >> .env
echo SQL_ENGINE=$SQL_ENGINE >> .env
echo SQL_DATABASE=$SQL_DATABASE >> .env
echo SQL_USER=$SQL_USER >> .env
echo SQL_PASSWORD=$SQL_PASSWORD >> .env
echo SQL_HOST=$SQL_HOST >> .env
echo SQL_PORT=$SQL_PORT >> .env
echo DATABASE=$DATABASE >> .env
echo AMPLITUDE_API_KEY=$AMPLITUDE_API_KEY >> .env
echo GITHUB_RUN_ID=$GITHUB_RUN_ID >> .env
echo WEB_IMAGE=${{ env.WEB_IMAGE }} >> .env
echo NAMESPACE=${{ secrets.NAMESPACE }} >> .env
echo PERSONAL_ACCESS_TOKEN=${{ secrets.PERSONAL_ACCESS_TOKEN }} >> .env
