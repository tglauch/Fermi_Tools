#!/usr/bin/env python
# coding: utf-8
import numpy as np
import os
import argparse
import sys
from configobj import ConfigObj
from os.path import exists, join


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mem",
        help="memory for job",
        type=int, default=6)
    parser.add_argument(
        "--tbin",
        help="Length of time bins for LC in days",
        type=int, default=-1)
    parser.add_argument(
        "--bpath",
        help="basepath for data, config files and saving",
        type=str, required=True)
    parser.add_argument(
        "--emin",
        help="The minimum energy for the analysis",
        type=float, default=-1)
    parser.add_argument(
        "--time_range",
        help="The minimum energy for the analysis",
        type=float, required=True, nargs="+")
    parser.add_argument(
        "--target_src",
        help="The target source",
        type=str, required=True)
    parser.add_argument(
        "--srcmdl",
        help="Name of the source model file",
        type=str, default="model.xml")
    parser.add_argument(
        "--photon_prob",
        help="Probability of photons belonging to a source",
        action='store_false')
    parser.add_argument(
        "--free_pars",
        help="The free parameters of the target source",
        type=str, default=["all"], nargs="+")
    parser.add_argument(
        "--free_radius",
        help="Free sources in a radius of X degrees around the source",
        type=float, default=-1)
    parser.add_argument(
        "--group",
        help="Name of accounting group",
        type=str, default="None")
    return parser.parse_args().__dict__


args = parseArguments()
if args['tbin'] == -1:
    args['tbin'] = args['time_range'][1] - args['time_range'][0]
time_bins = np.arange(args['time_range'][0],
                      args['time_range'][1],
                      args['tbin'])
executable = './env.sh'
log_str = 'job'
for i in range(len(time_bins)):
    tmin = time_bins[i]
    if (i + 1) < len(time_bins):
        tmax = time_bins[i + 1]
    else:
        tmax = args['time_range'][1]
    print('Time Range: {} - {}'.format(tmin, tmax))
    out_folder = join('./', 'results', args['bpath'],
                      '{}_{}'.format(tmin, tmax), str(int(args['emin'])))
    if not os.path.exists(out_folder):
        print('Create a Directory in {}'.format(out_folder))
        os.makedirs(out_folder)
    sub_args = ""
    for key in args.keys():
        if key == 'mem' or key == 'time_range' or key == 'tbin' or key == 'group':
            continue
        elif key == 'photon_prob':
            if args['photon_prob']:
                sub_args += ' --photon_prob '
        elif key == "free_pars":
                sub_args += ' --free_pars {} '.format(" ".join(args['free_pars'])) 

        else:
            sub_args += " --{} {}".format(key, args[key])
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
