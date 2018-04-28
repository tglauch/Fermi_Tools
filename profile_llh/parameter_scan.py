#!/usr/bin/env python
# coding: utf-8
import os
import argparse
from os.path import join
import gt_apps as gt_app
import pyLikelihood
from UnbinnedAnalysis import *
import numpy as np
import functions


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
        "--index",
        help="Spectral Index of the target source",
        type=float, required=True)
    return parser.parse_args().__dict__


args = parseArguments()

settings = functions.prepare_settings(args)
print('---- Settings ----')
print(settings)
print('\n \n Starting the Analysis ... \n')
settings = functions.prepare_ana_files(settings)

# LLH Fit
print(settings)

norm_bins = np.linspace(0.001, 0.035, 30)
index_bins = args['index']

obs = UnbinnedObs(settings['evfile'], settings['scfile'],
                  expMap=settings['expmap'], expCube=settings['ltcube'],
                  irfs=settings['irfs'])
TS = []

for norm in norm_bins:
    like = UnbinnedAnalysis(obs, settings['srcmdl'],
                            optimizer=settings['optimizer'])
    likeobj = pyLike.NewMinuit(like.logLike)
    print('Prefactor: {}, Spectral Index: {}'.format(norm, index_bins))
    spec = like[settings['target_src']].spectrum()
    spec.getParam('Prefactor').setValue(norm)
    spec.getParam('Index').setValue(index_bins)
    like.freeze(like.par_index(settings['target_src'], 'Prefactor'))
    like.freeze(like.par_index(settings['target_src'], 'Index'))
    for i in range(args['minimizations']):
        print('Run Fit number: {}'.format(i))
        like.fit(verbosity=0, covar=True, optObject=likeobj)
        negative_ts = 0
        for source in like.sourceNames():
            ts = like.Ts(source)
            if ts < 0:
                if not source == settings['target_src']:
                    like.deleteSource(source)
                    negative_ts += 1
        if (negative_ts) == 0 and (likeobj.getRetCode() == 0):
            print('Fit has converged...no negative TS values')
            break
    print('TS: {}'.format(like.Ts(settings['target_src'])))
    TS.append(like.Ts(settings['target_src']))

print('Search Best-Fit model')

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
                negative_ts += 1
    if (negative_ts) == 0 and (likeobj.getRetCode() == 0):
        print('Fit has converged...no negative TS values')
        break

odict = dict()
param_names = like[settings['target_src']]['Spectrum'].__dict__['paramNames']
spec = like[settings['target_src']].spectrum()
for key in param_names:
    element = spec.getParam(key)
    odict[element.getName()] = {'value': element.getValue(),
                                'scale': element.getScale(),
                                'error': element.error()}
odict['TS'] = like.Ts(settings['target_src'])

res_dict = {'ts': TS,
            'norm': norm_bins,
            'index': index_bins,
            'best_fit': odict}

np.save('./ts_grid_out/ts_space_{}.npy'.format(index_bins), res_dict)
