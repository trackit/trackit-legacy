#!/usr/bin/env bash

DOCKER=$(which docker)
DOCKER_COMPOSE=$(which docker-compose)

function osx {
    DOCKER_MACHINE=$(which docker-machine)
    HOST=$($DOCKER_MACHINE ip)
}

function linux {
    HOSTNAME=$(which hostname)
    HOST=$($HOSTNAME -i)
}

function not_supported {
    echo "Your OS is not supported yet."
}

case "$OSTYPE" in
  darwin*)  osx ;;
  linux*)   linux ;;
  *)        not_supported ;;
esac

export TRACKIT_HOST=$HOST
$DOCKER pull "msolution/trackit_ui:latest"
$DOCKER pull "msolution/trackit_api:latest"
$DOCKER_COMPOSE up -d
echo "TrackIt has been launched on http://$HOST/ !"
