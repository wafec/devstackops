#!/bin/bash


rm /etc/hosts

touch /etc/hosts
echo -e "127.0.0.1\tlocalhost" >> /etc/hosts

for i in $(seq 1 9); do
    echo -e "$NETWORK.2$i\tcompute$i" >> /etc/hosts
done

if [[ "$HOST" -gt "20" ]]; then
    index=$(echo "$HOST" | cut -c2-3)
    sed -i "/compute$index/d" /etc/hosts
    echo -e "127.0.0.1\tcompute$index" >> /etc/hosts
    echo -e "$NETWORK.$SERVICE_HOST\tcontroller" >> /etc/hosts
    hostnamectl set-hostname compute$index
elif [[ "$HOST" -gt "10" ]]; then
    echo -e "127.0.0.1\tcontroller" >> /etc/hosts
    hostnamectl set-hostname controller
else
    echo "Invalid host"
fi


netplan_file='/etc/netplan/02-devstack.yaml'
rm -rf $netplan_file
touch $netplan_file
echo "network:" >> $netplan_file
echo "  version: 2" >> $netplan_file
echo "  renderer: networkd" >> $netplan_file
echo "  ethernets:" >> $netplan_file
echo "    enp0s3:" >> $netplan_file
echo "      dhcp4: yes" >> $netplan_file
echo "    enp0s8:" >> $netplan_file
echo "      dhcp4: no" >> $netplan_file
echo "      addresses:" >> $netplan_file
echo "      - $NETWORK.$HOST/24" >> $netplan_file

netplan apply