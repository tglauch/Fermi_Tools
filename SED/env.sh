#!/bin/bash

#source /scratch9/tglauch/realtime_service/myfermi/bin/activate
source /scratch9/tglauch/realtime_service/myfermiv11/bin/activate
export PYTHONPATH='/home/ga53lag/Software/python_scripts':$PYTHONPATH
export FERMI_DIR='/home/ga53lag/Software/ScienceTools-v11r5p3-fssc-20180124-x86_64-unknown-linux-gnu-libc2.17/x86_64-unknown-linux-gnu-libc2.17'
#export FERMI_DIR='/home/ga53lag/Software/ScienceTools-v10r0p5-fssc-20150518-x86_64-unknown-linux-gnu-libc2.17/x86_64-unknown-linux-gnu-libc2.17'
source $FERMI_DIR/fermi-init.sh
python /scratch9/tglauch/Fermi_Tools/SED/run_SED_fit.py $@ 
