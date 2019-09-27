#!/bin/bash

if [ "$#" -ne 3 ]; then
  echo "Please provide 3 arguments"
  exit 1
fi

branch=$1
repo=$(pwd)
inet=$2
mode=$3
cloneurl=https://github.com/openstack-dev/devstack
cachegroup=$(stat -c "%G" ~/.cache)

if [ "$EUID" -ne 0 ]; then
  echo "Please you need to run as a root user to proceed"
  exit
fi

sudo ifconfig $inet 192.168.56.31 netmask 255.255.255.0
sudo apt update
sudo apt install virtualbox-guest-dkms -y
sudo delgroup stack
sudo deluser stack
if [ "$mode" == "init" ]; then
  sudo rm -rf /opt/stack
  echo "/opt/stack removed"
fi
sudo useradd -s /bin/bash -d /opt/stack -m stack
sudo usermod -a -G $cachegroup stack
chmod +775 ~/.cache
sudo apt install git -y
sudo rm -f /etc/sudoers.d/stack
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack
branchfile=$(echo "$branch" | sed -e "s/\//-/g")
if [ -d "/opt/stack/devstack" ] && [ ! -f "/opt/stack/devstack/$branchfile" ]; then
  sudo rm -fr /opt/stack/devstack
  echo "/opt/stack/devstack removed"
fi
if [ ! -f "/opt/stack/devstack/$branchfile" ]; then
  su -l stack -c "git clone -b $branch $cloneurl /opt/stack/devstack"
  su -l stack -c "echo \"Branch $branch cloned!\" | tee /opt/stack/devstack/$branchfile"
  echo "Branch $branch cloned and file $branchfile saved"
fi

cp local.conf /opt/stack/devstack/local.conf
if [ "$mode" == "unstack" ] || [ "$mode" == "clear" ] || [ "$mode" == "init" ] || [ "$mode" == "stack" ]; then
  su -l stack -c "/opt/stack/devstack/unstack.sh"
fi
if [ "$mode" == "clear" ] || [ "$mode" == "init" ]; then
  su -l stack -c "/opt/stack/devstack/clear.sh"
fi
if [ "$mode" == "stack" ] || [ "$mode" == "clear" ] || [ "$mode" == "init" ] || [ "$mode" == "stack" ]; then
  su -l stack -c "/opt/stack/devstack/stack.sh"
fi

