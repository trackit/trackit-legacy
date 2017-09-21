#!/bin/sh

set -e

cd /usr/share/nginx/html/

# Replace all occurences of `trackit.io` by the contentso of TRACKIT_DOMAIN
# This is dangerous and ugly but changing the Javascript configuration alone
# does not change all occurences.
# TODO: Ensure config.js actually changes all occurences, and make it modifiable
#       at the time the container is run
API_TRACKIT_DOMAIN=$(echo ${API_TRACKIT_DOMAIN} | sed "s./.\\\/.g")
ENABLE_FORGOTTEN_PASSWORD=$(echo ${ENABLE_FORGOTTEN_PASSWORD} | sed "s./.\\\/.g")
LOGIN_ONLY_EMAIL=$(echo ${LOGIN_ONLY_EMAIL} | sed "s./.\\\/.g")
find . -type f | xargs sed -i -re "s/\bENV\.API_TRACKIT_DOMAIN\b/$API_TRACKIT_DOMAIN/g"
find . -type f | xargs sed -i -re "s/\bENV\.ENABLE_FORGOTTEN_PASSWORD\b/$ENABLE_FORGOTTEN_PASSWORD/g"
find . -type f | xargs sed -i -re "s/\bENV\.LOGIN_ONLY_EMAIL\b/$LOGIN_ONLY_EMAIL/g"

nginx -g 'daemon off;'
