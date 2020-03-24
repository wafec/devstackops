#!/bin/bash

USER_NAME=${USER_NAME:-stack}
USER_HOME=${USER_HOME:-/opt/stack}
DEVSTACK_BRANCH=${DEVSTACK_BRANCH:-stable/train}
DEVSTACK_REPO_URL=${DEVSTACK_REPO_URL:-https://opendev.org/openstack/devstack}
NETWORK=${NETWORK:-192.168.56}
CONTROLLER_HOST=$HOST
SERVICE_HOST=${SERVICE_HOST:-HOST}
FIXED_RANGE=${FIXED_RANGE:-10.4.128.0/20}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-aintasecret}
SUPER_PASSWORD=${SUPER_PASSWORD:-supersecret}
DATABASE_TYPE=${DATABASE_TYPE:-mysql}


get_conf_file() {
    echo "$USER_HOME/$DEVSTACK_BRANCH/devstack/local.conf"
}

get_devstack() {
    echo "$USER_HOME/$DEVSTACK_BRANCH/devstack"
}

get_dest() {
    echo "$USER_HOME/$DEVSTACK_BRANCH"
}
