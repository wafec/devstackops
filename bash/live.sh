#!/bin/bash


copy_key_files() {
    DEST=$1
    USER=$2
    GROUP=$3
    sudo rm -rf $DEST/.ssh
    sudo mkdir $DEST/.ssh
    sudo cp key/* $DEST/.ssh
    sudo chown -R $USER:$GROUP $DEST/.ssh
    sudo chmod 400 $DEST/.ssh/id_rsa
    sudo chmod 400 $DEST/.ssh/id_rsa.pub
    sudo chmod 400 $DEST/.ssh/config
}


copy_key_files /root root root
copy_key_files /opt/stack stack stack