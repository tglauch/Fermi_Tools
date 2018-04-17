#!/usr/bin/env python
# coding: utf-8

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
	"--mode",
	help="list of Fermi analysis tools, i.e. gtlike, gtdiffrsp, gttsmap ",
	nargs="+", type=str, required=True)
    parser.add_argument(
	"--trange",
	help="give a time range", nargs="+",
	type=int, required=True)
    parser.add_argument(
	"--bpath",
	help="basepath for data, config files and saving",
	type=str, required=True)
    parser.add_argument(
        "--project",
        help="The name of the project, is also used for the save folder",
        type=str, default='some_project')
    parser.add_argument(
	"--model",
	help="the model xml file for TS maps fitting",
	type=str, default='diffuse.xml')
    parser.add_argument(
	"--emin",
	help="The minimum energy for the analysis",
	type=float, default=-1)
    parser.add_argument(
        "--group",
        help = "Name of accounting group",
        type=str, default="None")
    return parser.parse_args().__dict__


args = parseArguments()
config = ConfigObj(join('./',args['bpath'], 'analysis.cfg'))
model = config['src_model']
if args['emin'] == -1:
    emin = config['emin']
else:
    emin = args['emin']
print 'Mode: {}'.format(args['mode'])
print 'Time Range: {}'.format(args['trange'])
print 'emin : {}'.format(emin)
out_folder = join('./', args['bpath'], '{}_{}'.format(args["trange"][0], args["trange"][1]), args['project'])
if not os.path.exists(out_folder):
    os.makedirs(out_folder)
if 'gtlike' in args['mode']:
    log_str = config['src_model'][:-4]
    executable = './run_analysis.sh'
    if exists(join(out_folder, 'fit_model.xml')):
	print('removing old fit result...')
	os.remove(join(out_folder, 'fit_model.xml'))
elif 'gttsmap' in args['mode']:
    executable = './create_TS_map.sh'
    if args['model']=='diffuse.xml':
	ts_model = join(os.path.dirname(os.path.realpath(__file__)), 'diffuse.xml')
    else:
	ts_model = join(os.path.dirname(os.path.realpath(__file__)), args['bpath'],
                        '{}_{}'.format(args["trange"][0], args["trange"][1]),
                        args['project'], args['model'])
    print('TS Model: {}'.format(ts_model))
else:
    raise Exception('The given mode is not valid')

if 'gtdiffrsp' in args['mode']:
    print('Remove Diffuse Response...') 
    print(join(out_folder, model))
    os.remove(join(out_folder, model))
sub_args = "{} {} {}".format(args["bpath"], args["trange"][0], args["trange"][1])
if 'gttsmap' in args['mode']:
    log_str = args['model'][:-4]
    sub_args+=' {} {}.fits'.format(ts_model, args['model'][:-4])
sub_args+=' {}'.format(args['project'])
if 'gtlike' in args['mode']:
    sub_args += ' {}'.format(emin)
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
if args['group']!='None':
    print('Use AccountingGroup: {}'.format(args['group']))
    submit_info="AccountingGroup={} \n".format(args['group'])+submit_info
sub_file = '{}.sub'.format(log_str)
with open(sub_file, "wc") as file:
	file.write(submit_info)

os.system("condor_submit {}".format(sub_file))
os.rename('./{}'.format(sub_file), join(out_folder, sub_file))

