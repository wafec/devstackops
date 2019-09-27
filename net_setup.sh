#!/bin/bash

source "./check_sudo.sh"

inet=$1

name=devstacknet
ifpath=/etc/network/if-up.d

echo "#!/bin/sh" | sudo tee /etc/init.d/$name | sudo tee $ifpath/$name
echo "ifconfig $inet 192.168.56.31 netmask 255.255.255.0" | sudo tee -a $ifpath/$name
sudo chmod +x $ifpath/$name
