#!/usr/bin/env bash

hash "docker"  2> /dev/null || { echo >&2 "docker not found, exiting."; exit; }
hash "docker-compose"  2> /dev/null || { echo >&2 "docker-compose not found, exiting."; exit; }

DOCKER=$(which docker)
DOCKER_COMPOSE=$(which docker-compose)

function osx {
    hash "docker-machine"  2> /dev/null || { echo >&2 "docker-machine not found, exiting."; exit; }
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
