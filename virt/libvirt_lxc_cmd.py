#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Guido Günther <agx@sigxcpu.org>
#
# This module is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see
# <http://www.gnu.org/licenses/>.

import sys
import datetime
import shlex
import os

import xml.etree.ElementTree as ET


DOCUMENTATION = '''
---
module: cmd
short_description: Executes a command in a libvirt lxc container
description:
     - The M(libvirt_lxc_cmd) module takes the command name followed by a list of space-delimited arguments.
     - The given command will be run via libvirt-lxc's
       lxc-enter-namespace feature in the given container. It will not
       be processed through the shell, so variables like C($HOME) and
       operations like C("<"), C(">"), C("|"), and C("&") will not
       work.
options:
  cmd:
    description:
      - The command to run
    required: true
    default: None
  container:
    description:
      - Execute command in this container
    required: true
    default: None
  creates:
    description:
      - File creted by this command. If this file already exists the
        command will be skipped. Path is relative to the container root.
  unless:
    description:
      - If this parameter is set, then this command will run unless the
        command has an exit code of 0
  onlyif:
    description:
      - If this parameter is set, then this command will only run if the
        command has an exit code of 0
  conn:
    description:
      - cd into this directory before running the command
    required: false
    default: lxc:///
author: 
    - Guido Günther
'''

EXAMPLES = '''
# Run command in container cont1
- libvirt_lxc_cmd: /sbin/shutdown -t now container=cont1

# You can also use the 'args' form to provide the options.
- command: /sbin/shutdown -t now
  args:
    container: cont1

# Stop cron inside the container if running
- command: /bin/systemctl stop cron
  args:
    container: cont1
    onlyif: /bin/systemctl status cron
'''

VIRSH='virsh'


def container_root(domain):
    rc, domxml, err = module.run_command([VIRSH, '-c', conn, 'dumpxml', domain])

    if rc:
        module.fail_json(msg="Failed to get domain xml for '%s': %s" % (domain, err))

    xmlroot = ET.fromstring(domxml)
    filesystems = xmlroot.findall(".//devices/filesystem")
    for fs in filesystems:
        t = fs.find('target')
        if t is not None:
            if t.attrib.get('dir', None) == '/':
                return fs.find('source').attrib['dir']
    return None


def check_exists(creates, domain):
    """Return True if the file exists relative to the container root"""
    root = container_root(domain)
    if not root:
        module.fail_json(msg="Failed to get container root for '%s'" % domain)
    # Make this a relative path, otherwise os.path.join will silently drop
    # the first part
    hostpath = os.path.join(root, creates.lstrip('/'))
    return os.path.exists(hostpath)


def run_command_in_container(cmd, domain):
    args = shlex.split(cmd)
    virsh_cmd = ['virsh', '-c', conn, 'lxc-enter-namespace', '--noseclabel',  domain, '--cmd' ] + args
    rc, out, err = module.run_command(virsh_cmd)
    return (virsh_cmd, rc, out or '', err or '')


def main():
    global conn, module

    # the libvirt_lxc_cmd module is the one ansible module that does
    # not take key=value args hence don't copy this one if you are
    # looking to build others!
    module = AnsibleModule(
        argument_spec  = dict(
            cmd        = dict(required=True),
            container  = dict(required=True),
            conn       = dict(required=False, default="lxc:///"),
            creates    = dict(required=False),
            unless     = dict(required=False),
            onlyif     = dict(required=False),
        )
    )

    cmd = module.params['cmd']
    container  = module.params['container']
    conn  = module.params['conn']
    creates = module.params['creates']
    unless = module.params['unless']
    onlyif = module.params['onlyif']

    if cmd.strip() == '':
        module.fail_json(rc=256, msg="no command given")

    args = shlex.split(cmd)
    virsh_args = ['virsh', '-c', conn, 'lxc-enter-namespace', '--noseclabel',  container, '--cmd' ] + args

    if len([x for x in [creates, unless, onlyif] if x is not None]) not in [0, 1]:
        module.fail_json(msg="Unless, creates and onlyif can't be given at the same time.")

    if creates:
        # Do nothing if the file already exists
        if check_exists(creates, container):
            module.exit_json(
                cmd      = virsh_args,
                changed  = False,
            )

    if unless:
        # Do nothing if unless returns 0
        cmd, rc, out, err = run_command_in_container(unless, container)
        if not rc:
            module.exit_json(
                msg      = "Skipped since %s return 0" % unless,
                stdout   = out.rstrip("\r\n"),
                stderr   = err.rstrip("\r\n"),
                cmd      = cmd,
                changed  = False,
            )

    if onlyif:
        # Do nothing if unless returns 0
        cmd, rc, out, err = run_command_in_container(onlyif, container)
        if rc:
            module.exit_json(
                msg      = "Skipped since %s did not return 0" % onlyif,
                stdout   = out.rstrip("\r\n"),
                stderr   = err.rstrip("\r\n"),
                cmd      = cmd,
                changed  = False,
            )

    startd = datetime.datetime.now()
    rc, out, err = module.run_command(virsh_args)
    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = ''
    if err is None:
        err = ''

    module.exit_json(
        cmd      = virsh_args,
        stdout   = out.rstrip("\r\n"),
        stderr   = err.rstrip("\r\n"),
        rc       = rc,
        start    = str(startd),
        end      = str(endd),
        delta    = str(delta),
        changed  = True,
    )

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    sys.exit(main())
