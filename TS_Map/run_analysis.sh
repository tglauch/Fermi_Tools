#!/bin/bash
cd $1
export FERMI_DIR=/data/user/tglauch/Software/ScienceTools-v10r0p5-fssc-20150518-x86_64-unknown-linux-gnu-libc2.12/x86_64-unknown-linux-gnu-libc2.12
export LATEXTDIR=/data/user/tglauch/Software/ScienceTools-v10r0p5-fssc-20150518-x86_64-unknown-linux-gnu-libc2.12/x86_64-unknown-linux-gnu-libc2.12/xml/fermi/ext_srcs/Extended_archive_v15
source $FERMI_DIR/fermi-init.sh
dir=$2_$3/$4 
mkdir -p $dir
ev_file=./data/events.txt
sc_file=./data/spacecraft.fits
cd data
find `pwd` -name '*PH*' > events.txt
if [ -s  *SC* ]
then
    mv *SC* spacecraft.fits
fi
cd ..
source analysis.cfg
MJDREF=51910.0007429
mjd_min=$(echo "($2-$MJDREF)*86400." | bc )
mjd_max=$(echo "($3 - $MJDREF)*86400." | bc)
echo $mjd_min
echo $mjd_max

if [ ! -s $dir/filtered.fits ]
then
	gtselect infile=$ev_file outfile=$dir/filtered.fits ra=$ra dec=$dec rad=$radius evclass=128 evtype=3 tmin=$mjd_min tmax=$mjd_max  emin=$5 emax=$emax zmax=100
fi

if [ ! -s $dir/filtered_gti.fits ]
then
	gtmktime scfile=$sc_file filter="DATA_QUAL>0 && LAT_CONFIG==1" roicut=no evfile=$dir/filtered.fits outfile=$dir/filtered_gti.fits
fi

if [ ! -s $dir/ltcube.fits ]
then
	echo "Calculate gtltcube"
	gtltcube evfile=$dir/filtered_gti.fits scfile=$sc_file outfile=$dir/ltcube.fits dcostheta=0.025 binsz=1 zmax=90
fi

if [ ! -s $dir/unbin_expmap.fits ]
then
	echo "Calculate Exposure Map"
	gtexpmap evfile=$dir/filtered_gti.fits scfile=$sc_file expcube=$dir/ltcube.fits outfile=$dir/unbin_expmap.fits irfs=CALDB srcrad=20 nlong=120 nlat=120 nenergies=$ebins
fi

if [ ! -s $dir/$src_model ]
then
	cp $src_model $dir/$src_model
	echo "Calculate Diffuse Response"
	gtdiffrsp evfile=$dir/filtered_gti.fits scfile=$sc_file srcmdl=$dir/$src_model irfs=CALDB
fi

echo "Perform Likelihood Analysis"
gtlike irfs=CALDB expcube=$dir/ltcube.fits srcmdl=$dir/$src_model \
       statistic=UNBINNED optimizer=$minimizer evfile=$dir/filtered_gti.fits \
       scfile=$sc_file expmap=$dir/unbin_expmap.fits \
       sfile=$dir/fit_model.xml results=$dir/results.dat \
       specfile=$dir/counts_spectra.fits chatter=4
