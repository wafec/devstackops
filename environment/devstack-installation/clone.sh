#!/bin/bash

create_branch_directory() {
    su -l $USER_NAME -c "mkdir -p $USER_HOME/$DEVSTACK_BRANCH"
}

clone_project() {
    destination=$(get_devstack)
    su -l $USER_NAME -c "git clone -b $DEVSTACK_BRANCH $DEVSTACK_REPO_URL $destination"
    if [ -f "$destination/local.sh" ]; then
        su -l $USER_NAME -c "cp $destination/local.sh $destination/local.sh.bkp"
    else
        su -l $USER_NAME -c "touch $destination/local.sh"
        su -l $USER_NAME -c "touch $destination/local.sh.bkp"
    fi
}


if [ ! -d "$USER_HOME/$DEVSTACK_BRANCH" ]; then
    create_branch_directory
fi

if [ ! -d "$USER_HOME/$DEVSTACK_BRANCH/devstack" ]; then
    clone_project
fi