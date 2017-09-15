#!/bin/bash

set -e

tag="$(date '+%Y-%m-%d')-$(git show --pretty=format:%h | head -n1)"
repository='394125495069.dkr.ecr.us-west-2.amazonaws.com/trackit'

for dockerfile in Dockerfile.nomad.*
do
	service=$(sed -re 's/^Dockerfile\.nomad\.(.*)*/\1/' <<< "${dockerfile}")
	image="${repository}/${service}:${tag}"
	ln -fs $dockerfile Dockerfile
	docker build -t "${image}" .
	docker push "${image}" &
done
