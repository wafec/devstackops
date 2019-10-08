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