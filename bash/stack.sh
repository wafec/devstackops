#!/bin/bash

NUMBER_RE='^[0-9]+$'
if [[ "$#" -gt 2 ]] || [[ ! "$1" =~ $NUMBER_RE ]]; then
    echo "Invalid arguments"
    exit
fi

HOST=$1

if [[ "$1" -gt "20" ]] && [[ "$#" -eq 2 ]]; then
    if [[ "$2" =~ $NUMBER_RE ]]; then
        SERVICE_HOST=$2
    else
        echo "Invalid arguments"
        exit
    fi
else
    if [[ ! "$#" -eq 1 ]]; then
        echo "Invalid arguments"
        exit
    fi
fi

stack_compute() {
    source compute.sh $HOST
}

stack_controller() {
    source controller.sh
}


source validate.sh
source common.sh
source user.sh
source host.sh
source clone.sh

if [ "$HOST" -gt "20" ]; then
    stack_compute
elif [[ "$HOST" -gt "10" ]] && [[ "$HOST" -lt "20" ]]; then
    stack_controller
else
    echo "Invalid host"
    exit
fi

DEVSTACK=$(get_devstack)

su -l $USER_NAME -c "$DEVSTACK/stack.sh"

source live.sh