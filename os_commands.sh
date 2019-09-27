#!/bin/bash

sudo apt install python3

export OS_AUTH_URL=http://192.168.56.31/identity/v3
export OS_COMPUTE_URL=http://192.168.56.31/compute/v2.1

# getting the TOKEN
curl -v -s -X POST $OS_AUTH_URL/auth/tokens -H "Content-type: application/json" -d @auth.json | python3 -m json.tool

# then, copy the x-auth token and test it
export OS_TOKEN=# <-- token HERE
curl -v -s -X GET $OS_COMPUTE_URL/servers -H "X-Auth-Token: $OS_TOKEN"