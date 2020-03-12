#!/bin/bash


rm /etc/hosts

touch /etc/hosts
echo -e "127.0.0.1\tlocalhost" >> /etc/hosts

for i in $(seq 1 9); do
    echo -e "192.168.56.2$i\tcompute$i" >> /etc/hosts
done

if [[ "$HOST" -gt "20" ]]; then
    index=$(echo "$HOST" | cut -c2-3)
    sed -i "/compute$index/d" /etc/hosts
    echo -e "127.0.0.1\tcompute$index" >> /etc/hosts
    echo -e "192.168.56.$SERVICE_HOST\tcontroller" >> /etc/hosts
elif [[ "$HOST" -gt "10" ]]; then
    echo -e "127.0.0.1\tcontroller" >> /etc/hosts
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
echo "      - 192.168.56.$HOST/24" >> $netplan_file

netplan apply


apt install -y openssh-server
su -l $USER_NAME -c "
    rm -rf ~/.ssh
    mkdir ~/.ssh
    eval $(ssh-agent -s)
    sleep 1
    cp $(pwd)/key/id_rsa ~/.ssh/id_rsa
    cp $(pwd)/key/id_rsa.pub ~/.ssh/id_rsa.pub
    chmod 400 ~/.ssh/id_rsa
    ssh-add ~/.ssh/id_rsa
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    cp $(pwd)/key/config ~/.ssh/config
    chmod 400 ~/.ssh/config
"