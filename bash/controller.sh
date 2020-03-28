#!/bin/bash

CONF_FILE=$(get_conf_file)
DEST=$(get_dest)

if [ -f "$CONF_FILE" ]; then
    su -l $USER_NAME -c "rm $CONF_FILE"
fi

su -l $USER_NAME -c "touch $CONF_FILE"
su -l $USER_NAME -c "echo \"[[local|localrc]]\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"HOST_IP=$NETWORK.$CONTROLLER_HOST\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"FIXED_RANGE=$FIXED_RANGE\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"FLOATING_RANGE=$NETWORK.128/25\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"LOGFILE=$USER_HOME/logs/$USER_NAME.sh.log\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"ADMIN_PASSWORD=$ADMIN_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"DATABASE_PASSWORD=$SUPER_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"RABBIT_PASSWORD=$SUPER_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"SERVICE_PASSWORD=$SUPER_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"DEST=$DEST\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"OS_IDENTITY_API_VERSION=3\" >> $CONF_FILE"
#su -l $USER_NAME -c "echo \"USE_PYTHON3=True\" >> $CONF_FILE"
#su -l $USER_NAME -c "echo \"PYTHON3_VERSION=3.6\" >> $CONF_FILE"
#su -l $USER_NAME -c "echo \"PIP_UPGRADE=True\" >> $CONF_FILE"

DEVSTACK=$(get_devstack)

if [ -f "$DEVSTACK/local.sh.bkp" ]; then
    su -l $USER_NAME -c "rm $DEVSTACK/local.sh"
    su -l $USER_NAME -c "cp $DEVSTACK/local.sh.bkp $DEVSTACK/local.sh"

    su -l $USER_NAME -c "echo \"for i in `seq 2 10`; do $USER_HOME/nova/bin/nova-manage fixed reserve 10.4.128.\$i; done\" >> $DEVSTACK/local.sh"
fi