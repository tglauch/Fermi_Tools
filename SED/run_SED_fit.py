# coding: utf-8

from fermipy.gtanalysis import GTAnalysis
import numpy as np
import os
import argparse
import yaml
import pickle

MJDREF = 51910.0 + 7.428703703703703E-4


@np.vectorize
def MJD_to_MET(mjd_time):
    return (mjd_time - MJDREF) * 86400.


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trange",
        help="give a time range", nargs="+",
        type=int, required=True)

    parser.add_argument(
        "--emin",
        help="The minimum energy for the analysis",
        type=float, default=100)

    parser.add_argument(
        "--target_src",
        help="The target source for the analysis",
        type=str, default='3FGL_J0509.4+0541')

    parser.add_argument(
        "--retries",
        help="Number of retries if fit does not converge",
        type=int, default=5)

    parser.add_argument(
        "--free_sources",
        help="define which sources to fit",
        type=str, nargs="+", required=False)

    parser.add_argument(
        "--src_gamma",
        help="choose a fixed gamma for the target source",
        type=float, required=False)

    parser.add_argument(
        "--free_radius",
        help="free sources in a radius of the target source",
        type=float, required=False)
    return parser.parse_args().__dict__


args = parseArguments()
src = args['target_src'].replace('_', ' ')
print("Running with args \n")
print(args)

emin = args['emin']
basepath = './results/{}_{}/{}/'.format(args['trange'][0],
                                        args['trange'][1],
                                        emin)
if not os.path.exists(basepath):
    os.makedirs(basepath)

# Create Config File
config_path = os.path.join(basepath, 'config.yaml')

with open('default.yaml', 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
config['selection']['emin'] = args['emin']
config['selection']['tmin'] = float(MJD_to_MET(args['trange'][0]))
config['selection']['tmax'] = float(MJD_to_MET(args['trange'][1]))
config['selection']['target'] = src

with open(config_path, 'w+') as stream:
    config = yaml.dump(config, stream, default_flow_style=False)


# Run Analysis
gta = GTAnalysis(os.path.join(basepath, 'config.yaml'),
                 logging={'verbosity': 3})
gta.setup()
gta.optimize()


#Configure Target Source
if not args['src_gamma'] is None:
    print('Set Gamma to {}'.format(args['src_gamma']))
    gta.set_parameter(src, "Index", args['src_gamma'])
    free_pars = 'norm'
else:
    free_pars = None
print('Fix the target source: {}'.format(src))
gta.free_source(src, pars=free_pars, free=True)

# LLH Fit to ROI model
if not args['free_radius'] is None:
    print('Free sources in {} deg radius'.format(args['free_radius']))
    gta.free_sources(distance=args['free_radius'])
elif not args['free_sources'] is None:
    for src_key in args['free_sources']:
        print('Free source {} \n'.format(src_key))
        gta.free_source(src_key)


# Free all parameters of isotropic and galactic diffuse components
gta.free_source('galdiff')
gta.free_source('isodiff')

out_dict = gta.fit(retries=args['retries'])

gta.write_roi('llh.npy')
x = np.load(os.path.join(basepath, 'llh.npy'))[()]
#index = x['sources'][src]['spectral_pars']['Index']['value']
#print('Use fitted spectral index (gamma = {}) for SED FIT'.format(index))

# Override the energy binning and the assumed power-law index
# within the bin
sed = gta.sed(src, outfile='sed.fits',
              loge_bins=list(np.arange(np.log10(emin), np.log10(1e6), 0.5))) #bin_index = index
#pickle.dump()
