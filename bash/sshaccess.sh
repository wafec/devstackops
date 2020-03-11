#!/bin/bash

if [ ! -d ~/.ssh ]; then
    mkdir ~/.ssh
fi
chmod 700 ~/.ssh
eval $(ssh-agent -s)
ssh-add id_rsa
cat id_rsa.pub > ~/.ssh/authorized_keys