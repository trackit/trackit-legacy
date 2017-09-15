#!/bin/sh -x

set -e

docker run \
	--rm \
	-i \
	--env=TRACKIT_DOMAIN="${DEPLOYMENT_DOMAIN}" \
	trackit/ui ./exportlandingtar.sh | tar x
aws s3 sync landing "s3://${DEPLOYMENT_PREFIX}-landing/"
