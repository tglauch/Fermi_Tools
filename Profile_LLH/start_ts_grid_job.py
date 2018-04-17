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
	type=int, default=2)
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
    return parser.parse_args().__dict__


args = parseArguments()
executable = './env_ts_grid.sh'
log_str = 'ts_grid_job'
index_r = np.linspace(0.7, 2.6, 30)
for ind in index_r:
	out_folder = join('./', args['bpath'], '{}_{}'.format(args['time_range'][0], args['time_range'][1]), str(int(args['emin'])))
	if not os.path.exists(out_folder):
	    os.makedirs(out_folder)
	sub_args = "--bpath {} --time_range {} {} --emin {} --target_src {} --index {}".format(args["bpath"], args['time_range'][0], args['time_range'][1],
                                                                                               args['emin'], args['target_src'], ind)
	print sub_args
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

	sub_file = '{}.sub'.format(log_str)
	with open(sub_file, "wc") as file:
		file.write(submit_info)

	os.system("condor_submit {}".format(sub_file))
	os.rename('./{}'.format(sub_file), join(out_folder, sub_file))

