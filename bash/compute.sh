#!/bin/bash

COMPUTE_HOST=$1
CONF_FILE=$(get_conf_file)
DEST=$(get_dest)

if [ -f $CONF_FILE ]; then
    su -l $USER_NAME -c "rm $CONF_FILE"
fi

su -l $USER_NAME -c "touch $CONF_FILE"
su -l $USER_NAME -c "echo \"[[local|localrc]]\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"HOST_IP=$NETWORK.$COMPUTE_HOST\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"FIXED_RANGE=$FIXED_RANGE\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"FLOATING_RANGE=$NETWORK.128/25\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"LOGFILE=$USER_HOME/logs/$USER_NAME.sh.log\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"ADMIN_PASSWORD=$ADMIN_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"DATABASE_PASSWORD=$SUPER_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"RABBIT_PASSWORD=$SUPER_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"SERVICE_PASSWORD=$SUPER_PASSWORD\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"DATABASE_TYPE=$DATABASE_TYPE\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"SERVICE_HOST=$NETWORK.$SERVICE_HOST\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"MYSQL_HOST=\\\$SERVICE_HOST\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"RABBIT_HOST=\\\$SERVICE_HOST\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"GLANCE_HOSTPORT=\\\$SERVICE_HOST:9292\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"ENABLED_SERVICES=n-cpu,q-agt,n-api-meta,c-vol,placement-client\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"NOVA_VNC_ENABLED=True\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"NOVNCPROXY_URL=\\\"http://\\\$SERVICE_HOST:6080/vnc_lite.html\\\"\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"VNCSERVER_LISTEN=\\\$HOST_IP\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"VNCSERVER_PROXYCLIENT_ADDRESS=\\\$VNCSERVER_LISTEN\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"USE_PYTHON3=True\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"PYTHON3_VERSION=3.4\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"DEST=$DEST\" >> $CONF_FILE"
su -l $USER_NAME -c "echo \"PIP_UPGRADE=True\" >> $CONF_FILE"
