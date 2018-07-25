# coding: utf-8

'''
Example Run:
python start_lc_jobs.py --tbin 55 --bpath 5BZB_J0211+1051 --emin 200 --time_range 54716 58156 --target_src 3FGL_J0211.2+1051 --srcmdl 5BZB_J0211+1051_logP.xml --data_path /data/user/tglauch/Fermi_Data/5BZB_J0211+1051/ --free_radius 3
'''

import time
import os
import argparse
import sys
from configobj import ConfigObj
from os.path import exists, join


def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mem",
        help="memory for job",
        type=int, default=2)
    parser.add_argument(
        "--tbin",
        help="Length of time bins for LC in days",
        type=int, default=-1)
    parser.add_argument(
        "--time_range",
        help="The time range for the lightcurve",
        type=float, required=True, nargs="+")
    parser.add_argument(
        "--group",
        help="Name of accounting group",
        type=str, default="None")
    parser.add_argument(
        "--executable",
        help="Choose and Executable File",
        required=True, type=str)
    args, unknown = parser.parse_known_args()
    return args.__dict__, unknown 


args, unkwn = parseArguments()
if args['tbin'] == -1:
    args['tbin'] = args['time_range'][1] - args['time_range'][0]
i0 = drange(args['time_range'][0],
                      args['time_range'][1],
                      args['tbin'])
time_bins = [x for x in i0]
print time_bins
executable = args['executable']
tm = time.localtime(time.time())
t_str='{}-{}-{}-{}-{}-{}'.format(tm.tm_year, tm.tm_mon, tm.tm_mday,
                                 tm.tm_hour, tm.tm_min, tm.tm_sec)
out_folder = join('./', 'condor' , t_str)
if not os.path.exists(out_folder):
    print('Create a Directory in {}'.format(out_folder))
    os.makedirs(out_folder)
 
for i in range(len(time_bins)):
    sub_args = ' '.join(unkwn)
    tmin = time_bins[i]
    if (i + 1) < len(time_bins):
        tmax = time_bins[i + 1]
    else:
        tmax = args['time_range'][1]
    print('Time Range: {} - {}'.format(tmin, tmax))
    log_str = 'job_{}_{}'.format(tmin, tmax)
    sub_args += " --time_range {} {} ".format(tmin, tmax)

    print('submit args: \n {}'.format(sub_args))
    submit_info = 'executable   = {script}  \n\
    universe     = vanilla  \n\
    request_memory = {mem}GB \n\
    log          = {out}/{logs}.log \n\
    output       = {out}/{logs}.out \n\
    error        = {out}/{logs}.err \n\
    arguments =  {args} \n\
    queue 1 \n '.format(script=executable,
                        mem=args['mem'],
                        args=sub_args,
                        logs=log_str,
                        out=out_folder)
    if args['group'] != 'None':
        print('Use AccountingGroup: {}'.format(args['group']))
        submit_info = "AccountingGroup={} \n".format(args['group']) + submit_info
    sub_file = '{}.sub'.format(log_str)
    with open(sub_file, "wc") as file:
        file.write(submit_info)

    os.system("condor_submit {}".format(sub_file))
    os.rename('./{}'.format(sub_file), join(out_folder, sub_file))
