#!/bin/bash


echo "In remote, who am I? $(whoami)"
echo "Destination: $DEST"

cd /root
eval $(ssh-agent -s)
if [ ! -f .ssh/id_rsa ]; then
    echo -e "\n\n\n" | ssh-keygen -t rsa 2>&1 > /dev/null
    ssh-add .ssh/rsa_id
fi
ssh-keyscan -H $DEST >> .ssh/known_hosts 2>&1 > /dev/null
echo -e "123" | ssh-copy-id -i .ssh/id_rsa.pub stack@$DEST