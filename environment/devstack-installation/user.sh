#!/bin/bash

create_user() {
    sudo useradd -s /bin/bash -d $USER_HOME -m $USER_NAME
    echo "$USER_NAME ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER_NAME
}

id -u $USER_NAME
user_exists=$?

if [ $user_exists -eq 1 ]; then
    create_user
fi

if [ -d "$USER_HOME/.cache" ]; then
    sudo rm -rf $USER_HOME/.cache
fi

su -l $USER_NAME -c "mkdir -p $USER_HOME/.cache"

DEST=$(get_dest)

if [ -d "$DEST/.cache" ]; then
    sudo rm -rf $DEST/.cache
fi

su -l $USER_NAME -c "mkdir -p $DEST/.cache"