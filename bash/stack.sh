#!/bin/bash

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

if [ "$HOST" -gt "20"]; then
    stack_compute()
elif [ "$HOST" -eq "11" ]; then
    stack_controller()
else
    echo "Invalid host"
    exit
fi

get_devstack()
DEVSTACK=$?
su -l $USER_NAME -c "$DEVSTACK/stack.sh"