# coding: utf-8

import requests
from mechanize import Browser
import argparse
import time
import os
import wget
import shutil
from myfunctions import MJD_to_MET
from astropy.io import fits
# Settings


def get_dl_links(html):
    split = html.split('wget')
    status = int(html.split('he state of your query is ')[1][:1])
    if status == 2:
        return [(i.split('</pre>'))[0].strip().replace('\n', '')
                for i in split[2:]]
    else:
        return []

def setup_data_files(folder, sc_file=None):
    files = os.listdir(folder)
    if 'events.txt' not in files:
        ph_files = [os.path.join(folder, f) for f in files if 'PH' in f]
        with open(os.path.join(folder, 'events.txt'), 'w+') as ofile:
            ofile.write("\n".join(ph_files))
    if sc_file is not None:
        os.symlink(sc_file, os.path.join(folder, 'spacecraft.fits'))
    else:
        if 'spacecraft.fits' not in files:
            sc_files = [f for f in files if 'SC' in f]
            if len(sc_files) == 1:
                os.rename(os.path.join(folder, sc_files[0]),
                          os.path.join(folder, 'spacecraft.fits'))
            else:
                raise Exception('No Spacecraft File Available!')
    return

def parseArguments():
    """Parse the command line arguments
    Returns:
    args : Dictionary containing the command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ra",
        help="right ascension",
        type=float, required=True)
    parser.add_argument(
        "--dec",
        help="declination",
        type=float, required=True)
    args = parser.parse_args()
    return args.__dict__

def get_data(ra, dec, sc_file=None, **kwargs):
    if kwargs.get('out_dir') is None:
        out_dir = './ra_{}_dec_{}'.format(ra, dec)
    else:
        out_dir = kwargs.get('out_dir')
    url = "https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi"
    if sc_file is None:
        html = requests.get(url).text.encode('utf8')
        MET = [i.strip() for i in html.split('(MET)')[1][:24].split('to')]
    else:
        print('Use SC file from {}'.format(sc_file))
        new_file = fits.open(sc_file)
        MET = [str(new_file[1].header['TSTART']), str(new_file[1].header['TSTOP'])]
    mjd_range = kwargs.get('mjd')
    if isinstance(mjd_range, float):
        days = kwargs.get('days')
        mode = kwargs.get('mode', 'end')

        if days is not None:
            if not MJD_to_MET(mjd_range)>float(MET[1]):
                MET[1] = str(MJD_to_MET(mjd_range))
            if mode == 'mid':
                MET[0] = str(float(MET[1]) - kwargs['days']/2. * 24 * 60 * 60)
                MET[1] = str(float(MET[1]) + kwargs['days']/2. * 24 * 60 * 60)
            elif mode == 'end':
                MET[0] = str(float(MET[1]) - kwargs['days'] * 24 * 60 * 60)
            else:
                raise ValueError('mode for mjd range must be mid or end, but {} was given'.format(mode))
    if isinstance(mjd_range, list):
        MET[0] = str(MJD_to_MET(mjd_range[0]))
        MET[1] = str(MJD_to_MET(mjd_range[1]))
    print MET
    br = Browser()
    br.set_handle_robots(False)
    br.open(url)
    br.select_form(nr=0)
    br["coordfield"] = '{ra} , {dec}'.format(ra=ra,
                                             dec=dec)
    br['coordsystem'] = [u'J2000']
    br['timetype'] = [u'MET']
    br['timefield'] = ', '.join(MET)
    br['shapefield'] = '8'
    br['energyfield'] = '{}, {}'.format(kwargs.get('emin', 100),
                                        kwargs.get('emax', 800000))
    if sc_file is not None:
        br.form.find_control('spacecraft').items[0].selected = False 
    response = br.submit()
    r_text = response.get_data()
    query_url = r_text.split('at <a href="')[1].split('"')[0]
    print('Query URL {}'.format(query_url))
    seconds = float(r_text.split('complete is ')[1].split(' ')[0])
    wait = 0.75 * seconds
    print('Wait at least {} seconds for the query to complete'.format(wait))
    time.sleep(wait)

    html = requests.get(query_url).text.encode('utf8')
    dl_urls = get_dl_links(html)
    while len(dl_urls) == 0:
        print('Query not yet finished...Wait 10 more seconds')
        time.sleep(10)
        html = requests.get(query_url).text.encode('utf8')
        dl_urls = get_dl_links(html)

    print('Downloading the following list of files:')
    print dl_urls
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    for url in dl_urls:
        wget.download(url, out=out_dir)
    setup_data_files(out_dir, sc_file=sc_file)
    return MET


if __name__ == '__main__':
    args = parseArguments()
    get_data(args['ra'], args['dec'])
