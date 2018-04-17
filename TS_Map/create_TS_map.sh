#!/bin/bash
cd $1
export FERMI_DIR=/data/user/tglauch/Software/ScienceTools-v10r0p5-fssc-20150518-x86_64-unknown-linux-gnu-libc2.12/x86_64-unknown-linux-gnu-libc2.12
export LATEXTDIR=/data/user/tglauch/Software/ScienceTools-v10r0p5-fssc-20150518-x86_64-unknown-linux-gnu-libc2.12/x86_64-unknown-linux-gnu-libc2.12/xml/fermi/ext_srcs/Extended_archive_v15
source $FERMI_DIR/fermi-init.sh
source analysis.cfg
sc_file=./data/spacecraft.fits
dir=$2_$3/$6
gttsmap statistic=UNBINNED evfile=$dir/filtered_gti.fits scfile=$sc_file \
  expmap=$dir/unbin_expmap.fits expcube=$dir/ltcube.fits srcmdl=$4 \
  outfile=$dir/$5 irfs=CALDB optimizer=DRMNGB ftol=1e-05 \
  nxpix=$npix nypix=$npix binsz=$bins xref=$ra yref=$dec \
  coordsys=CEL proj=STG \
