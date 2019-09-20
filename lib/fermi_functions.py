# coding: utf-8

from fermipy.gtanalysis import GTAnalysis
import sys
sys.path.append('/home/ga53lag/Software/python_scripts/')
import numpy as np
import os
import yaml
import pyfits as fits
from myfunctions import MET_to_MJD, MJD_to_MET
import argparse

def setup_data_files(folder):
    files = os.listdir(folder)
    if 'events.txt' not in files:
        ph_files = [os.path.join(folder, f) for f in files if 'PH' in f]
        with open(os.path.join(folder, 'events.txt'), 'w+') as ofile:
            ofile.write("\n".join(ph_files))
    if 'spacecraft.fits' not in files:
        sc_files = [f for f in files if 'SC' in f]
        if len(sc_files) == 1:
            os.rename(os.path.join(folder, sc_files[0]),
                      os.path.join(folder, 'spacecraft.fits'))
        else:
            raise Exception('No Spacecraft File Available!')
    return


def get_time_window(folder):
    files = os.listdir(folder)
    files = [f for f in files if 'PH' in f]
    tmin = []
    tmax = []
    for f in files:
        x = fits.open(os.path.join(folder, f))
        tmin.append(x[1].header['TSTART'])
        tmax.append(x[1].header['TSTOP'])
    return float(np.min(tmin)), float(np.max(tmax))


def setup_gta(args):
    src = args['target_src'].replace('_', ' ')
    print("Running with args \n")
    print(args)

    emin = args['emin']
    emax = args['emax']
    if args['time_range'] is not None:
        print('Use Self-Defined Time Window')
        tmin = float(MJD_to_MET(args['time_range'][0]))
        tmax = float(MJD_to_MET(args['time_range'][1]))
    else:
        print('Use Entire Time Window Available')
        tmin, tmax = get_time_window(args['data_path'])
    this_path = os.path.dirname(os.path.abspath(__file__))
    if args['outfolder'] is not None:
        basepath = args['outfolder']
    else:
        add_path = '{:.0f}_{:.0f}/{}_{}/'.format(
                   args['target_src'],
                   float(MET_to_MJD(tmin)),
                   float(MET_to_MJD(tmax)),
                   int(emin), int(emax))
        basepath = os.path.join(this_path, add_path)
    setup_data_files(args['data_path'])
    if not os.path.exists(basepath):
        os.makedirs(basepath)

    # Create Config File
    config_path = os.path.join(basepath, 'config.yaml')

    with open(os.path.join(this_path, 'default.yaml'), 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    config['selection']['emin'] = emin
    config['selection']['emax'] = emax
    config['selection']['tmin'] = tmin
    config['selection']['tmax'] = tmax
    if args['roiwidth'] is not None:
       config['binning']['roiwidth'] = args['roiwidth'] 
    if src != '':
        config['selection']['target'] = src
    elif ('ra' in args) and ('dec' in args):
        config['selection']['ra'] = args['ra']
        config['selection']['dec'] = args['dec']
    config['data']['evfile'] = \
        os.path.join(args['data_path'], config['data']['evfile'].split('/')[-1])
    config['data']['scfile'] = \
        os.path.join(args['data_path'], config['data']['scfile'].split('/')[-1])
    config['model']['catalogs'] = []
    if args['xml_path'] is not None:
        config['model']['catalogs'].append('{}'.format(args['xml_path']))
    if args['use_3FGL']:
        config['model']['catalogs'].append('3FGL')
    if args['use_4FGL']:
        config['model']['catalogs'].append('4FGL')
    with open(config_path, 'w+') as stream:
        config = yaml.dump(config, stream, default_flow_style=False)
    # Run Analysis
    gta = GTAnalysis(os.path.join(basepath, 'config.yaml'),
                     logging={'verbosity': 3})
    gta.setup()
    gta.print_params(True)
    gta.optimize()
    #  Free all parameters of isotropic and galactic diffuse components
    if args['free_diff']:
        print('Free Diffuse Components')
        gta.free_source('galdiff', pars='norm')
        gta.free_source('isodiff', pars='norm')
    if src == '':
        gta.optimize()
        return gta, basepath
    if not args['free_radius'] is None:
        print('Free sources in {} deg radius (with TS>2)'.format(args['free_radius']))
 
        gta.free_sources(distance=args['free_radius'],
                         minmax_ts=[2, None],
                         exclude=['isodiff', 'galdiff'])
    elif not args['free_sources'] is None:
        for src_key in args['free_sources']:
            print('Free source {} \n'.format(src_key))
            gta.free_source(src_key)

    # Configure Target Source
    if  args['src_gamma'] is not None:
        print('Set Gamma to {}'.format(args['src_gamma']))
        gta.set_parameter(src, "Index", args['src_gamma'])
        free_pars = 'norm'
    elif args['free_norm']:
        free_pars = 'norm'
    else:
        free_pars = None
    print('Free the target source: {} with pars: {}'.format(src, free_pars))
    gta.free_source(src, pars=None, free=False)
    gta.free_source(src, pars=free_pars, free=True)
    gta.print_params(True)
    return gta, basepath, src, free_pars

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--time_range",
        help="give a time range", nargs="+",
        type=float, required=False)
    parser.add_argument(
        "--emin",
        help="The minimum energy for the analysis",
        type=float, default=100)
    parser.add_argument(
        "--emax",
        help="The minimum energy for the analysis",
        type=float, default=800000)
    parser.add_argument(
        "--target_src",
        help="The target source for the analysis",
        type=str, default='')
    parser.add_argument(
        "--retries",
        help="Number of retries if fit does not converge",
        type=int, default=50)
    parser.add_argument(
        "--free_sources",
        help="Define which sources are free for the fit",
        type=str, nargs="+", required=False)
    parser.add_argument(
        "--free_diff",
        help="Free the isotropic and galactic diffuse component",
        action='store_true', default=False)
    parser.add_argument(
        "--use_3FGL",
        help="Decide of whether or not to use 3FGL sources",
        action='store_true', default=False)
    parser.add_argument(
        "--use_4FGL",
        help="Decide of whether or not to use 4FGL sources",
        action='store_true', default=False)
    parser.add_argument(
        "--free_norm",
        help="Only free the normalization of the target",
        action='store_true', default=False)
    parser.add_argument(
        "--no_sed",
        help="Only run llh and bowtie, no sed points",
        action='store_true', default=False)
    parser.add_argument(
        "--src_gamma",
        help="choose a fixed gamma for the target source",
        type=float, required=False)
    parser.add_argument(
        "--free_radius",
        help="free sources in a radius of the target source",
        type=float, required=False)
    parser.add_argument(
        "--data_path",
        help="Path to the data files",
        type=str, required=True)
    parser.add_argument(
        "--xml_path",
        help="path to xml files with additional sources for the model",
        type=str, default=None)
    parser.add_argument(
         "--outfolder",
         help="where to save the output files?",
         type=str, required=False)
    parser.add_argument(
        "--ra",
        help="right ascension",
        type=float,)
    parser.add_argument(
        "--dec",
        help="dec",
        type=float)
    parser.add_argument(
        "--roiwidth",
        help="size of the roi",
        type=float)
    return parser.parse_args().__dict__
