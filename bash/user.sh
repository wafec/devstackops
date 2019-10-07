#!/bin/bash

create_user() {
    sudo useradd -s /bin/bash -d /opt/stack -m stack
    echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo /etc/sudoers.d/stack
}

id -u $USERNAME
user_exists=$?

if [[ $user_exists -eq 1 ]]; then
    create_user()
fi