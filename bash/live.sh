#!/bin/bash


sudo apt install -y sshpass
echo -e "123\n123" | sudo passwd stack
export EXT_HOST=$HOST
su --preserve-environment -c$(pwd)/live_root.sh root
su --preserve-environment -c$(pwd)/live_stack.sh stack