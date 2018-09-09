#!/bin/bash

#source '/data/user/tglauch/fermi_env/bin/activate'

export FERMI_DIR='/data/user/tglauch/Software/ScienceTools-v10r0p5-fssc-20150518-x86_64-unknown-linux-gnu-libc2.17/x86_64-unknown-linux-gnu-libc2.17'
source $FERMI_DIR/fermi-init.sh
python /data/user/tglauch/Fermi_Tools/SED/run_SED_fit.py $@ 
