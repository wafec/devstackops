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


apt install -y openssh-server
echo "$USER_NAME"
su -l $USER_NAME -c "rm -rf ~/.ssh"
su -l $USER_NAME -c "mkdir ~/.ssh" 
su -l $USER_NAME -c "cp $(pwd)/key/id_rsa ~/.ssh/id_rsa"
su -l $USER_NAME -c "cp $(pwd)/key/id_rsa.pub ~/.ssh/id_rsa.pub"
su -l $USER_NAME -c "cp $(pwd)/key/id_ecdsa ~/.ssh/id_ecdsa"
su -l $USER_NAME -c "cp $(pwd)/key/id_ecdsa.pub ~/.ssh/id_ecdsa.pub"
su -l $USER_NAME -c "chmod 400 ~/.ssh/id_rsa"
su -l $USER_NAME -c "chmod 400 ~/.ssh/id_ecdsa"
su -l $USER_NAME -c 'eval $(ssh-agent -s); ssh-add ~/.ssh/id_rsa; ssh-add ~/.ssh/id_ecdsa'
su -l $USER_NAME -c "cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys"
su -l $USER_NAME -c "cat ~/.ssh/id_ecdsa.pub >> ~/.ssh/known_hosts"
su -l $USER_NAME -c "cp $(pwd)/key/config ~/.ssh/config"
su -l $USER_NAME -c "chmod 400 ~/.ssh/config"

rm -rf /root/.ssh
mkdir /root/.ssh
cp ./key/config /root/.ssh/config
cat ./key/id_rsa.pub >> /root/.ssh/authorized_keys
cat ./key/id_ecdsa.pub >> /root/.ssh/known_hosts
chmod 400 /root/.ssh/config
chmod 400 /root/.ssh/authorized_keys
chmod 400 /root/.ssh/known_hosts
cp ./key/id_rsa.pub /root/.ssh/id_rsa.pub
cp ./key/id_ecdsa.pub /root/.ssh/id_ecdsa.pub
