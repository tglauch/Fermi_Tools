#!/usr/bin/env python
# coding: utf-8
import os
import argparse
from os.path import join
import gt_apps as gt_app
from GtApp import GtApp
import pyLikelihood
from UnbinnedAnalysis import *
from UpperLimits import UpperLimits
import numpy as np
import functions


def free_source(like, src, flux_models, free_pars=["all"]):
    src_spec = like[src].funcs['Spectrum']

    if free_pars[0] == "all": 
        pars = flux_models[src_info[src]['spec']]
    else:
        pars = free_pars

    for item in pars:
        src_spec.parameter(item).setFree(1)
    return


def prepare_output(like, settings):
    # assumens power-law spectral index for now

    target_src = settings['target_src']
    emin = settings['emin']
    emax = settings['emax']
    freeParValues = dict()
    for sourcename in like.sourceNames():
        if len(like.freePars(sourcename)) == 0:
            continue
        temp_dict = dict()
        param_names = like[sourcename]['Spectrum'].__dict__['paramNames']
        print param_names
        spec = like[sourcename].spectrum()
        for key in param_names:
            element = spec.getParam(key)
            temp_dict[element.getName()] = {'value': element.getValue(),
                                            'scale': element.getScale(),
                                            'error': element.error()}
        if sourcename == target_src:
            temp_dict['flux_100'] = like.flux(sourcename, emin=100)
            temp_dict['flux_100_err'] = like.fluxError(sourcename, emin=100)
            temp_dict['flux'] = like.flux(sourcename, emin=emin, emax=emax)
            temp_dict['flux_err'] = like.fluxError(sourcename, emin=emin,
                                                   emax=emax)
            temp_dict['eflux_100'] = like.energyFlux(sourcename, emin=100)
            temp_dict['eflux_100_err'] = like.energyFluxError(sourcename,
                                                              emin=100)
            temp_dict['eflux'] = like.energyFlux(sourcename, emin=emin,
                                                 emax=emax)
            temp_dict['eflux_err'] = like.energyFluxError(sourcename,
                                                          emin=emin,
                                                          emax=emax)
            temp_dict['npred'] = like.NpredValue(sourcename)
        temp_dict['TS'] = like.Ts(sourcename)
        freeParValues[sourcename] = temp_dict
    return freeParValues


def parseArguments():
    parser = argparse.ArgumentParser()
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
        help="The time range for the analysis",
        type=float, required=True, nargs="+")
    parser.add_argument(
        "--minimizations",
        help="Maximum Number of minimizations",
        type=float, required=False, default=10)
    parser.add_argument(
        "--config",
        help="Path to the Config File",
        type=str, required=False, default='settings.cfg')
    parser.add_argument(
        "--target_src",
        help="The target source",
        type=str, required=True)
    parser.add_argument(
        "--data_path",
        help="Path to the events.txt and spacecraft.fits file",
        type=str, default="/data/user/tglauch/Fermi_Data/TXS")
    parser.add_argument(
        "--srcmdl",
        help="Name of the source model file",
        type=str, default="model.xml")
    parser.add_argument(
        "--photon_prob",
        help="Probability of photons belonging to a source",
        action='store_false')
    parser.add_argument(
        "--ts_map",
        help="Which model to use for the TS map",
        type=str, default="None")
    parser.add_argument(
        "--free_pars",
        help="The free parameters of the target source",
        type=str, default=["all"], nargs="+")
    parser.add_argument(
        "--free_radius",
        help="Free sources in a radius of X degrees around the source",
        type=float, default=-1)
    return parser.parse_args().__dict__


args = parseArguments()
print('---- Run with args ----')
print(args)

settings = functions.prepare_settings(args)
print('\n---- Settings ----')
print(settings)
print('\n \n Starting the Analysis ... \n')
settings = functions.prepare_ana_files(settings)
src_info, flux_models = functions.get_source_info(settings)
print('\n Flux models used in the XML file:')
print(flux_models)

# LLH Fit
print(settings)

obs = UnbinnedObs(settings['evfile'], settings['scfile'],
                  expMap=settings['expmap'], expCube=settings['ltcube'],
                  irfs=settings['irfs'])

like = UnbinnedAnalysis(obs, settings['srcmdl'],
                        optimizer=settings['optimizer'])


free_source(like, settings['target_src'], flux_models, free_pars=args['free_pars'])

if args['free_radius'] != -1:
    for skey in src_info.keys():
        if src_info[skey]['dist'] < args['free_radius']:
            print("Free Source {}".format(skey))
            free_source(like, skey, flux_models)

likeobj = pyLike.NewMinuit(like.logLike)
for i in range(args['minimizations']):
    print('Run Fit number: {}'.format(i))
    like.fit(verbosity=0, covar=True, optObject=likeobj)
    negative_ts = 0
    for source in like.sourceNames():
        ts = like.Ts(source)
        if ts < 0:
            if not source == settings['target_src']:
                like.deleteSource(source)
                print('Deleted source {} with TS {}'.format(source, ts))
                negative_ts += 1
    if (negative_ts) == 0 and (likeobj.getRetCode() == 0):
        print('Fit has converged...no negative TS values')
        break
ul = UpperLimits(like)
ul[settings['target_src']].compute(emin=settings['emin'],
                                   emax=settings['emax'])
sourceDetails = {}
for source in like.sourceNames():
    sourceDetails[source] = like.Ts(source)
like.logLike.writeXml(join(settings['savefolder'], 'fit_model.xml'))
o_dict = prepare_output(like, settings)
print(ul[settings['target_src']])
o_dict[settings['target_src']]['UL'] = \
    ul[settings['target_src']].__dict__['results'][0].__dict__
np.save(join(settings['savefolder'], 'output.npy'), o_dict)
print('Finished...')

if args['photon_prob']:
    print("Calculate Photon Probabilities")
    gtsrcprob = GtApp('gtsrcprob')
    gtsrcprob['evfile'] = settings['evfile']
    gtsrcprob['scfile'] = settings['scfile']
    gtsrcprob['outfile'] = join(settings['savefolder'], 'photon_prob.fits')
    gtsrcprob['srcmdl'] = settings['srcmdl']
    gtsrcprob.run()


if args['ts_map'] != 'None':
    tsmap_pars = ['evfile', 'scfile', 'expmap', 'expcube', 'srcmdl', 'irfs', 'optimizer', 'binsz']
    for par in tsmap_pars:
        gt_app.TsMap[par] = settings[par]
    gt_app.TsMap['ftol'] = 1e-05
    gt_app.TsMap['coordsys'] = "CEL"
    gt_app.TsMap['proj'] = "STG"
    gt_app.TsMap['statistic'] = "UNBINNED"
    gt_app.TsMap['outfile'] = join(settings['savefolder'], 'ts_map.fits')
    gt_app.TsMap['nxpix'] = settings['nlong']
    gt_app.TsMap['nypix'] = settings['nlat']
    gt_app.TsMap['xref'] = settings['ra']
    gt_app.TsMap['yref'] = settings['dec']
    gt_app.run()

# print(like.freePars('target_src'))
