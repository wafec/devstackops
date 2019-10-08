#!/bin/bash

USER_NAME=stack
USER_HOME=/opt/stack
DEVSTACK_BRANCH=stable/rocky
DEVSTACK_REPO_URL=https://opendev.org/openstack/devstack
NETWORK=192.168.56
CONTROLLER_HOST=11
FIXED_RANGE=10.4.128.0/20
ADMIN_PASSWORD=labstack
SUPER_PASSWORD=supersecret
DATABASE_TYPE=mysql


get_conf_file() {
    get_conf_file=$USER_HOME/$DEVSTACK_BRANCH/devstack/local.conf
}

get_devstack() {
    get_devstack=$USER_HOME/$DEVSTACK_BRANCH/devstack
}