ansible-module-libvirt-lxc
==========================

Module to run commands in a libvirt-lxc container. E.g.:

    - libvirt_lxc_cmd:
        cmd: /sbin/shutdown -t now
        container: cont1

would run the shutdown command in container *cont1*. For idempotency you can
check if a file exists within the container. E.g.:

    - libvirt_lxc_cmd:
        cmd: /sbin/shutdown -t now
        container: cont1
        creates: /tmp/shutdown

only shuts down if /tmp/shutdown exists. The condition can also be a command
with onlyif:

    - libvirt_lxc_cmd:
        cmd: /sbin/shutdown -t now
        container: cont1
        onlyif: /bin/true

will only run the command given after only if exits zero. Unless does the
opposite

    - libvirt_lxc_cmd:
        cmd: /sbin/shutdown -t now
        container: cont1
        unless: /bin/false

This is pretty similar to what Puppet's [exec][] module does.


[exec]: https://docs.puppet.com/puppet/latest/reference/types/exec.html#exec-attributes
