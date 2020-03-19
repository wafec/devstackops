#!/bin/bash


export DEST=$1
echo -e "123\n123" | sudo passwd stack
su --preserve-environment -c $(pwd)/live_remote_root.sh root

