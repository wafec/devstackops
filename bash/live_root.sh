#!/bin/bash


configure_ssh() {
    echo "Testing connection with $1"
    ping -c 1 $1 2>&1 > /dev/null
    if [ $? -eq 0 ]; then
        echo "Configuring $1 SSH"
        ssh-keyscan -H $1 | sudo tee -a .ssh/known_hosts
        sshpass -p123 ssh-copy-id -i .ssh/id_rsa.pub stack@$1
        scp $2/live_remote.sh stack@$1:~/live_remote.sh
        scp $2/live_remote_root.sh stack@$1:~/live_remote_root.sh
        ssh stack@$1 "chmod +x live_remote.sh; chmod +x live_remote_root.sh;"
        ssh -t stack@$1 "sudo ./live_remote.sh $3"
        echo "Local configuration done"
    else
        echo "Connection test failed"
    fi
}


HOST=$EXT_HOST
echo "Who Am I? $(whoami)"
echo "Host: $HOST"
BASH_DIR=$(pwd)
cd /root
echo "Current dir: $(pwd)"

if [ ! -f .ssh/id_rsa ]; then
    mkdir .ssh
    ssh-keygen -t rsa -f .ssh/id_rsa -q -N ""
    eval $(ssh-agent -s)
    ssh-add .ssh/id_rsa
fi

source $BASH_DIR/index_utils.sh

if [[ ! $HOST_TYPE = "controller" ]]; then
    configure_ssh controller $BASH_DIR $HOST_NAME
fi

for i in $(seq 1 9); do
    if [ ! $i -eq $HOST_INDEX ] || [[ $HOST_TYPE = "controller" ]]; then
        configure_ssh "compute$i" $BASH_DIR $HOST_NAME
    fi
done