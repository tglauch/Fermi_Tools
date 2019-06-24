# coding: utf-8

from fermipy.gtanalysis import GTAnalysis
import sys
sys.path.append('/home/ga53lag/Software/python_scripts/')
sys.path.append('/scratch9/tglauch/Fermi_Tools/lib/')
import numpy as np
import os
import yaml
import pyfits as fits
from fermi_functions import parseArguments, setup_gta
from myfunctions import MET_to_MJD, MJD_to_MET


def run_fit(args):
    gta, basepath, src, free_pars  = setup_gta(args) 
    gta.fit(retries=args['retries'])
    gta.write_roi('llh.npy')

    print('Calculate Bowtie for {}'.format(src))
    bowtie = gta.bowtie(src)
    np.save(os.path.join(basepath, 'bowtie.npy'),
            bowtie)
    print('Start SED Fitting')
    # how to manage the parameter freeeing?
    print('Free the target source: {} with pars: {}'.format(src, free_pars))

    if not args['no_sed']:
        ofile = os.path.join(basepath, 'sed.fits'.format(int(args['emin']), int(args['emax'])))
        sed =gta.sed(src, outfile=ofile,
                     loge_bins=list(np.arange(np.log10(args['emin']),
                                    np.log10(args['emax']), 0.5)),
                     free_pars=free_pars,
                     free_radius=args['free_radius'],
                     free_background=True)

if __name__ == '__main__':
    args = parseArguments()
    run_fit(args)
