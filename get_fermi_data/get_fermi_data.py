#! /usr/bin/env python
# coding: utf-8

import requests
from mechanize import Browser
import argparse
import time
import os
import wget

# Settings


def get_dl_links(html):
    split = html.split('wget')
    status = int(html.split('he state of your query is ')[1][:1])
    print status
    if status == 2:
        return [i.strip().replace('\n', '')
                for i in split[1:-1]]
    else:
        return []


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

def get_data(ra, dec, emin=100, emax=800000, dt=-1,  out_dir=''):
    if out_dir == '':
        out_dir = './ra_{}_dec_{}'.format(ra, dec)
    url = "https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi"
    html = requests.get(url).text.encode('utf8')
    MET = [i.strip() for i in html.split('(MET)')[1][:24].split('to')]
    print MET
    if dt != -1:
        MET[0] = str(float(MET[1]) - dt * 24 * 60 * 60)
    br = Browser()
    br.set_handle_robots(False)
    br.open(url)
    br.select_form(nr=0)
    br["coordfield"] = '{ra} , {dec}'.format(ra=ra,
                                             dec=dec)
    br['coordsystem'] = [u'J2000']
    br['timetype'] = [u'MET']
    br['timefield'] = ', '.join(MET)
    br['shapefield'] = '15'
    br['energyfield'] = '{}, {}'.format(emin, emax)
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
        print('Query not finished...Wait 10 more seconds')
        time.sleep(10)
        dl_urls = get_dl_links(html)

    print('Downloading the following list of files:')
    print dl_urls
    #print('\n'.join(dl_urls))

    os.makedirs(out_dir)
    for url in dl_urls:
        wget.download(url, out=out_dir)


if __name__ == '__main__':
    args = parseArguments()
    get_data(args['ra'], args['dec'])
