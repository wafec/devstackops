#!/bin/bash


echo "In remote, who am I? $(whoami)"
echo "Destination: $DEST"

cd /root
eval $(ssh-agent -s)
if [ ! -f .ssh/id_rsa ]; then
    mkdir .ssh
    ssh-keygen -t rsa -f .ssh/id_rsa -q -N ""
    ssh-add .ssh/rsa_id
    chmod +r .ssh/rsa_id*
fi
ssh-keyscan -H $DEST | sudo tee -a .ssh/known_hosts
chmod +r .ssh/known_hosts
sshpass -p123 ssh-copy-id -i .ssh/id_rsa.pub stack@$DEST