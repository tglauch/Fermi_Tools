#!/usr/bin/env python
# coding: utf-8
import os
import argparse
from os.path import join
import gt_apps as gt_app
import pyLikelihood
from UnbinnedAnalysis import *
from UpperLimits import UpperLimits
import numpy as np
import functions


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
        help="The minimum energy for the analysis",
        type=float, required=True, nargs="+")
    parser.add_argument(
        "--minimizations",
        help="Maximum Number of minimizations",
        type=float, required=False, default=20)
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
        help = "Path to the events.txt and spacecraft.fits file",
        type=str, default="/data/user/tglauch/Fermi_Data/TXS")
    return parser.parse_args().__dict__


args = parseArguments()

settings = functions.prepare_settings(args)
print('---- Settings ----')
print(settings)
print('\n \n Starting the Analysis ... \n')
settings = functions.prepare_ana_files(settings)

# LLH Fit
print(settings)

obs = UnbinnedObs(settings['evfile'], settings['scfile'],
                  expMap=settings['expmap'], expCube=settings['ltcube'],
                  irfs=settings['irfs'])

like = UnbinnedAnalysis(obs, settings['srcmdl'],
                        optimizer=settings['optimizer'])

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
# print(like.freePars('target_src'))
