ansible-module-libvirt-lxc
==========================

Module to run commands in a libvirt-lxc container. E.g.:

	- libvirt_lxc_cmd: 
        cmd: /sbin/shutdown -t now
		container: cont1

would run the shutdown command in container *cont1*.
