#!/bin/bash


HOST=$EXT_HOST


SOURCE=$(pwd)
cd ~stack
DIR=$(pwd)
eval $(ssh-agent -s)
if [ ! -f $DIR/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -N "" -q -f $DIR/.ssh/id_rsa
    ssh-add $DIR/.ssh/id_rsa
fi

configure_ssh() {
    ping -c 1 $1 2>&1 > /dev/null
    if [ $? -eq 0 ]; then
        echo "Scanning $1"
        ECDSA=$(ssh-keyscan -H $1)

        if [ -f $DIR/.ssh/known_hosts ]; then
            if grep -q "$ECDSA" "$DIR/.ssh/known_hosts"; then
                echo "ECDSA was found in known hosts"
            else
                echo "Adding ECDSA to known hosts"
                echo $ECDSA | tee -a $DIR/.ssh/known_hosts
            fi
        fi

        echo "Copying SSH id to $1"
        sshpass -p123 sudo ssh-copy-id -i $DIR/.ssh/id_rsa.pub stack@$1
        echo "Copying files from $2 to remote"
        scp $2/live_stack_remote.sh stack@$1:~/live_stack_remote.sh
        scp $2/live_stack_remote_stack.sh stack@$1:~/live_stack_remote_stack.sh
        ssh stack@$1 "chmod +x live_stack_remote.sh; chmod +x live_stack_remote_stack.sh"
        echo "Running live stack remote scripts"
        ssh -t stack@$1 "sudo ./live_stack_remote.sh $3"
    else
        echo "Could not connect through SSH to $1"
    fi
}

echo "Who Am I? $(whoami)"

source $SOURCE/index_utils.sh

if [[ ! $HOST_TYPE = "controller" ]]; then
    configure_ssh controller $SOURCE $HOST_NAME
fi

for i in $(seq 1 9); do
    if [ ! $i -eq $HOST_INDEX ] || [[ $HOST_TYPE = "controller" ]]; then
        configure_ssh "compute$i" $SOURCE $HOST_NAME
    fi
done