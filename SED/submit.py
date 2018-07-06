#!/usr/bin/env python
# coding: utf-8

import os
import sys
from os.path import exists, join
import sys

sys_args = sys.argv[1:]
print sys_args
if '--long_queue' in sys_args:
    print('Use Long Queue')
    submit_info = 'AccountingGroup = 1_week \n'
    sys_args.remove('--long_queue')
else:
    print('Use Normal Queue')
    submit_info = ''
sub_args = ' '.join(sys_args)
print('Run args {}'.format(sub_args))
executable = './env.sh'

submit_info += ' executable   = {script}  \n\
universe     = vanilla  \n\
request_memory = {mem}GB \n\
log          = /dev/null \n\
output       = ./error.out \n\
error        = ./error.err \n\
arguments =  {args} \n\
queue 1 \n '.format(script=executable,
		    mem=2,
		    args=sub_args)
print submit_info
sub_file = 'submit_info.sub'
with open(sub_file, "wc") as file:
	file.write(submit_info)

os.system("condor_submit {}".format(sub_file))
