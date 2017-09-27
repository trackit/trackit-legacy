#!/bin/bash

function check_if_program_is_installed {
    CMD_PATH=$(command -v $1)
    if [ $? -ne 0 ]
    then
        echo "$1"
    else
        echo $CMD_PATH
    fi
}

DOCKER=$(check_if_program_is_installed "docker")
DOCKER_COMPOSE=$(check_if_program_is_installed "docker-compose")

if [ "$DOCKER" == "docker" ] || [ "$DOCKER_COMPOSE" == "docker-compose" ]
then
    echo "Docker or docker-compose is not installed"
    exit 
fi

if [ -z "$TRACKIT_HOST" ]
then
    export TRACKIT_HOST="localhost"
fi

$DOCKER pull "msolution/trackit_ui:latest"
$DOCKER pull "msolution/trackit_api:latest"
$DOCKER_COMPOSE up -d && echo "TrackIt has been launched on http://$TRACKIT_HOST/ !"
