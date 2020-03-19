#!/bin/bash


configure_ssh() {
    echo "Testing connection with $1"
    ping -c 1 $1 2>&1 > /dev/null
    if [ $? -eq 0 ]; then
        echo "Configuring $1 SSH"
        ssh-keyscan -H $1 >> .ssh/known_hosts 2>&1 > /dev/null
        echo -e "123" | ssh-copy-id -i .ssh/id_rsa.pub stack@$1
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
    echo -e "\n\n\n" | ssh-keygen -t rsa 2>&1 > /dev/null
    eval $(ssh-agent -s)
    ssh-add .ssh/id_rsa
fi

HOST_TYPE="controller"
HOST_INDEX=$(echo "$HOST" | cut -c2-3)
HOST_NAME="controller"

if [[ "$HOST" -gt "20" ]]; then
    HOST_TYPE="compute"
    HOST_NAME="compute$HOST_INDEX"
fi

echo "Host Type: $HOST_TYPE"
echo "Host Index: $HOST_INDEX"
echo "Host Name: $HOST_NAME"

if [[ ! $HOST_TYPE = "controller" ]]; then
    configure_ssh controller $BASH_DIR $HOST_NAME
fi

for i in $(seq 1 9); do
    if [ ! $i -eq $HOST_INDEX ] || [[ $HOST_TYPE = "controller" ]]; then
        configure_ssh "compute$i" $BASH_DIR $HOST_NAME
    fi
done