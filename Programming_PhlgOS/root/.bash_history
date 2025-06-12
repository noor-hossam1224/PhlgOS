ps -p 1 -o comm=
mount -t proc proc /proc
ps -p 1 -o comm=
exit
apt search sysvinit-core
apt search openrc
apt search runit
exit
