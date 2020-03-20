#!/bin/bash


export DESTINATION=$1
echo "Live stack remote script started"
echo "Destination: $DESTINATION"
su --preserve-environment -c$(pwd)/live_stack_remote_stack.sh stack

