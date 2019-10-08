#!/bin/bash

NUMBER_RE='^[0-9]+$'
if [[ "$#" -ne 1 ]] || [[ ! "$1" =~ $NUMBER_RE ]]; then
    echo "Invalid arguments"
    exit
fi

HOST=$1

stack_compute() {
    source compute.sh $HOST
}

stack_controller() {
    source controller.sh
}


source validate.sh
source common.sh
source user.sh
source clone.sh

if [ "$HOST" -gt "20" ]; then
    stack_compute
elif [[ "$HOST" -gt "11" ]] && [[ "$HOST" -lt "20" ]]; then
    stack_controller
else
    echo "Invalid host"
    exit
fi

DEVSTACK=$(get_devstack)

su -l $USER_NAME -c "$DEVSTACK/stack.sh"