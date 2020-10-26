#!/bin/bash
eval `/cvmfs/icecube.opensciencegrid.org/py2-v2/setup.sh`
export FERMI_DIR='/home/ga53lag/Software/ScienceTools-v11r5p3-fssc-20180124-x86_64-unknown-linux-gnu-libc2.17/x86_64-unknown-linux-gnu-libc2.17'
echo $FERMI_DIR
source $FERMI_DIR/fermi-init.sh
python pylightcurve.py $@ 
