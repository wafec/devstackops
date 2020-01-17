#!/bin/bash

if ! [[ -d ./data ]]; then
    echo 'Data folder not found'
    exit -1
fi

sudo rabbitmqctl list_bindings > ./data/bindings

if ! [[ -$? -eq 0 ]]; then
    exit -1
fi

echo 'Bindings copied successfully'