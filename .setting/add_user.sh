groupadd $1
useradd -p "123456" $1 -g $1
echo "$1:123456" | chpasswd
echo "$1 ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers