#!/bin/sh

set -e

cd /usr/share/nginx/html/

# Replace all occurences of `trackit.io` by the contentso of TRACKIT_DOMAIN
# This is dangerous and ugly but changing the Javascript configuration alone
# does not change all occurences.
# TODO: Ensure config.js actually changes all occurences, and make it modifiable
#       at the time the container is run
find . -type f | xargs perl -i -p \
	-e "s/(?<!blog\.)\btrackit\.io\b/${TRACKIT_DOMAIN}/g"
find landing/ -type f | xargs sed -i -r \
	-e "s/\"\\/#/\"https:\\/\\/app.${TRACKIT_DOMAIN}\\/#/g"

tar c landing/
