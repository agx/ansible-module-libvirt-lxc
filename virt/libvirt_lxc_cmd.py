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
import traceback
import shlex
import os

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
- libvirt_lxc_cmd: 
  cmd: /sbin/shutdown -t now
  container: cont1
'''

VIRSH='virsh'

def main():
    # the libvirt_lxc_cmd module is the one ansible module that does
    # not take key=value args hence don't copy this one if you are
    # looking to build others!
    module = AnsibleModule(
        argument_spec  = dict(
            cmd        = dict(required=True),
            container  = dict(required=True),
            conn       = dict(required=False, default="lxc:///"),
        )
    )

    cmd = module.params['cmd']
    container  = module.params['container']
    conn  = module.params['conn']

    if cmd.strip() == '':
        module.fail_json(rc=256, msg="no command given")

    args = shlex.split(cmd)
    virsh_args = ['virsh', '-c', conn, 'lxc-enter-namespace', '--noseclabel',  container, '--cmd' ] + args

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

main()
