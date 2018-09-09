# coding: utf-8

from fermipy.gtanalysis import GTAnalysis
import numpy as np
import os
import argparse
import yaml
import pickle
import pyfits as fits

   
def setup_data_files(folder):
    files = os.listdir(folder)
    if 'events.txt' not in files:
        ph_files = [os.path.join(folder,f) for f in files if 'PH' in f]
        with open(os.path.join(folder,'events.txt'), 'w+') as ofile:
            ofile.write("\n".join(ph_files))
    if not 'spacecraft.fits' in files:
        sc_files = [f for f in files if 'SC' in f]
        if len(sc_files)==1:
            os.rename(os.path.join(folder,sc_files[0]),
                      os.path.join(folder,'spacecraft.fits'))
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


MJDREF = 51910.0 + 7.428703703703703E-4
@np.vectorize
def MJD_to_MET(mjd_time):
    return float((mjd_time - MJDREF) * 86400.)

@np.vectorize
def MET_to_MJD(met_time):
    return float(met_time/86400.+MJDREF)

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
        type=str, default='3FGL_J0509.4+0541')

    parser.add_argument(
        "--retries",
        help="Number of retries if fit does not converge",
        type=int, default=20)

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
        type=str, required=False)
    return parser.parse_args().__dict__


args = parseArguments()
src = args['target_src'].replace('_', ' ')
this_path = os.path.dirname(os.path.abspath(__file__))
print("Running with args \n")
print(args)

emin = args['emin']
emax = args['emax']
if args['time_range'] is not None:
     print('Use Self-Defined Time Window')
     tmin = MJD_to_MET(args['time_range'][0])
     tmax = MJD_to_MET(args['time_range'][1])
else:
     print('Use Entire Time Window Available')
     tmin, tmax =  get_time_window(args['data_path'])

basepath = './results/{}/{:.0f}_{:.0f}/{}_{}/'.format(args['target_src'],
                                        float(MET_to_MJD(tmin)),
                                        float(MET_to_MJD(tmax)),
                                        int(emin), int(emax))
basepath = os.path.join(this_path, basepath)
setup_data_files(args['data_path'])
if not os.path.exists(basepath):
    os.makedirs(basepath)

# Create Config File
config_path = os.path.join(basepath, 'config.yaml')

with open(os.path.join(this_path,'default.yaml'), 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
config['selection']['emin'] = emin
config['selection']['emax'] = emax
config['selection']['tmin'] = tmin
config['selection']['tmax'] = tmax
config['selection']['target'] = src
config['data']['evfile'] = os.path.join(args['data_path'], config['data']['evfile'].split('/')[-1]) 
config['data']['scfile'] = os.path.join(args['data_path'], config['data']['scfile'].split('/')[-1])
config['model']['catalogs'] = []
if args['xml_path'] is not None:
    config['model']['catalogs'].append(args['xml_path'])
if args['use_3FGL']:
    config['model']['catalogs'].append('3FGL')
with open(config_path, 'w+') as stream:
    config = yaml.dump(config, stream, default_flow_style=False)


# Run Analysis
gta = GTAnalysis(os.path.join(basepath, 'config.yaml'), logging={'verbosity': 3})
gta.setup()


if not args['free_radius'] is None:
    print('Free sources in {} deg radius (with TS>2)'.format(args['free_radius']))
    gta.free_sources(distance=args['free_radius'], minmax_ts=[2,None], exclude = ['isodiff', 'galdiff'])
elif not args['free_sources'] is None:
    for src_key in args['free_sources']:
        print('Free source {} \n'.format(src_key))
        gta.free_source(src_key)

#Configure Target Source
if not args['src_gamma'] is None:
    print('Set Gamma to {}'.format(args['src_gamma']))
    gta.set_parameter(src, "Index", args['src_gamma'])
    free_pars = 'norm'
elif args['free_norm']:
    free_pars = 'norm'
else:
    gta.optimize()
    free_pars = None
print('Free the target source: {} with pars: {}'.format(src, free_pars))
gta.free_source(src, pars=None, free=False)
gta.free_source(src, pars=free_pars, free=True)


# Free all parameters of isotropic and galactic diffuse components
if args['free_diff']:
    print('Free Diffuse Components')
    gta.free_source('galdiff', pars='norm')
    gta.free_source('isodiff', pars='norm')
gta.fit(retries=args['retries'])
gta.write_roi('llh_emin_{}_emax_{}.npy'.format(int(emin), int(emax)))

print('Calculate Bowtie for {}'.format(src))
out_dict = gta.bowtie(src)
np.save(os.path.join(basepath, 'bowtie_emin_{}_emax_{}.npy'.format(int(emin), int(emax))), out_dict)
print('Start SED Fitting')
print('Free the target source: {} with pars: {}'.format(src, free_pars))

if not  args['no_sed']:
    sed = gta.sed(src, outfile='sed_emin_{}_emax_{}.fits'.format(int(emin), int(emax)),
                  loge_bins=list(np.arange(np.log10(emin), np.log10(emax), 0.5)),
	          free_pars=free_pars,
                  free_radius = args['free_radius']) #bin_index = index
#pickle.dump()
