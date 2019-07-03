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
    gta, basepath = setup_gta(args) 
    gta.compute_srcprob()
    return

if __name__ == '__main__':
    args = parseArguments()
    run_fit(args)
