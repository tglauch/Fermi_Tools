#!/bin/bash

#source '/data/user/tglauch/fermi_env/bin/activate'

eval `/cvmfs/icecube.opensciencegrid.org/py2-v2/setup.sh`
export FERMI_DIR='/data/user/tglauch/Software/ScienceTools-v11r5p3-fssc-20180124-x86_64-unknown-linux-gnu-libc2.17/x86_64-unknown-linux-gnu-libc2.17'
echo $FERMI_DIR
source $FERMI_DIR/fermi-init.sh
PYTHONPATH=/cvmfs/icecube.opensciencegrid.org/py2-v3/RHEL_7_x86_64/lib/python2.7/site-packages:$PYTHONPATH
python /data/user/tglauch/Fermi_Tools/SED/run_SED_fit.py $@ 
