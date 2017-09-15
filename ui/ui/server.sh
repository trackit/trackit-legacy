#!/bin/sh

set -e

cd /usr/share/nginx/html/

# Replace all occurences of `trackit.io` by the contentso of TRACKIT_DOMAIN
# This is dangerous and ugly but changing the Javascript configuration alone
# does not change all occurences.
# TODO: Ensure config.js actually changes all occurences, and make it modifiable
#       at the time the container is run
API_TRACKIT_DOMAIN=$(echo ${API_TRACKIT_DOMAIN} | sed "s./.\\\/.g")
find . -type f | xargs sed -i -re "s/\btrackit\.io\b/${TRACKIT_DOMAIN}/g"
find . -type f | xargs sed -i -re "s/\bblog\.${TRACKIT_DOMAIN}\b/blog\.trackit\.io/g"
find . -type f | xargs sed -i -re "s/\bENV\.API_TRACKIT_DOMAIN\b/$API_TRACKIT_DOMAIN/g"

nginx -g 'daemon off;'
