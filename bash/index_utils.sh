#!/bin/bash


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