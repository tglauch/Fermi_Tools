#!/bin/bash
eval `/cvmfs/icecube.opensciencegrid.org/py2-v2/setup.sh`
export FERMI_DIR='/data/user/tglauch/Software/ScienceTools-v10r0p5-fssc-20150518-x86_64-unknown-linux-gnu-libc2.12/x86_64-unknown-linux-gnu-libc2.12'
echo $FERMI_DIR
source $FERMI_DIR/fermi-init.sh
python parameter_scan.py $@ 
