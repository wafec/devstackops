#!/bin/bash


SOURCE=$(pwd)
cd ~stack
echo "Who am I in remote? $(whoami)"
echo "Working in $(pwd)"

eval $(ssh-agent -s)
if [ ! -f .ssh/id_rsa ]; then
    echo "Generating RSA file"
    ssh-keygen -t rsa -N "" -q -f .ssh/id_rsa
    ssh-add .ssh/id_rsa
    sudo chmod +r .ssh/id_rsa*
fi

echo "Scanning $DESTINATION"
ECDSA=$(ssh-keyscan -H $DESTINATION)

if grep -q "$ECSDA" ".ssh/known_hosts"; then
    echo "ECDSA was found in known hosts"
else
    echo "Adding ECDSA to known hosts"
    echo $ECDSA | tee -a .ssh/known_hosts
    ssh-keyscan -H $(getent hosts $DESTINATION | awk '{print $1}') | tee -a .ssh/known_hosts
fi

sudo chmod +r .ssh/known_hosts

echo "Copying SSH id to $DESTINATION"
sshpass -p123 sudo ssh-copy-id -i .ssh/id_rsa stack@$DESTINATION
