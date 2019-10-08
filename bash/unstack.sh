#!/bin/bash

source validate.sh
source common.sh

DEVSTACK=$(get_devstack)
if [[ -d "$DEVSTACK" ]] && [[ -f "$DEVSTACK/unstack.sh" ]]; then
    su -l $USER_NAME -c "$DEVSTACK/unstack.sh"
else
    echo "File not found"
fi