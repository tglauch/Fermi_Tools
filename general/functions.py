import os
from os.path import exists, join, abspath
import gt_apps as gt_app
from shutil import copyfile
import configparser
from ast import literal_eval
import xml.etree.ElementTree as ET
import numpy as np


def MJD_to_MET(mjd_time):
    MJDREF = 51910.0 + 7.428703703703703E-4
    return (mjd_time - MJDREF) * 86400.


def GreatCircleDistance(ra_1, dec_1, ra_2, dec_2):
    '''Compute the great circle distance between two events'''
    delta_dec = np.abs(dec_1 - dec_2)
    delta_ra = np.abs(ra_1 - ra_2)
    x = (np.sin(delta_dec / 2.))**2. + np.cos(dec_1) *\
        np.cos(dec_2) * (np.sin(delta_ra / 2.))**2.
    return 2. * np.arcsin(np.sqrt(x))


def get_source_info(settings):
    tree = ET.parse(settings['src_mdl_origin'])
    root = tree.getroot()
    src_info = dict()
    flux_models = dict()
    ra = settings['ra']
    dec = settings['dec']
    for src in root.getchildren():
        t_dict = dict()
        src_name = src.attrib['name']
        spectrum = src.find('spectrum')
        location = src.find('spatialModel')
        if not location.attrib['type'] == "SkyDirFunction":
            continue
        for coord in location.getchildren():
            t_dict[coord.attrib['name']] = coord.attrib['value']
        t_dict['dist'] = np.degrees(GreatCircleDistance(
                                    np.radians(ra), np.radians(dec),
                                    np.radians(float(t_dict['RA'])),
                                    np.radians(float(t_dict['DEC']))))
        t_dict['spec'] = spectrum.attrib['type']
        if spectrum.attrib['type'] not in flux_models.keys():
            tlist = []
            for child in spectrum.findall('parameter'):
                if child.attrib['name'] != 'Scale' and child.attrib['name'] != 'Eb':
                    tlist.append(child.attrib['name'])
            flux_models[spectrum.attrib['type']] = tlist
        src_info[src_name] = t_dict
    return src_info, flux_models


def get_src_pos(xml_file, target_src):
    pos = dict()  # ra,dec
    root = ET.parse(xml_file).getroot()
    for child in root.getchildren():
        if child.attrib['name'] == target_src:
            spat_model = child.find('spatialModel')
            for i in spat_model.iter():
                if not i.tag == 'parameter':
                    continue
                pos[i.attrib['name']] = i.attrib['value']
    return pos


def prepare_settings(args):

    savefolder = join('.', 'results', args['bpath'],
                      '{}_{}'.format(args['time_range'][0],
                       args['time_range'][1]), str(int(args['emin'])))

    if not exists(savefolder):
        print('Create Folder in {}'.format(savefolder))
        os.makedirs(savefolder)

    config = configparser.ConfigParser()
    config.read(join('.', 'config', args['config']))
    settings = dict()
    for key in config['Settings']:
        try:
            settings[str(key)] = literal_eval(config['Settings'][key])
        except Exception:
            settings[str(key)] = str(config['Settings'][key])
    settings['target_src'] = args['target_src'].replace('_', ' ')
    print settings['target_src']
    datafolder = args['data_path']
    settings['infile'] = join(datafolder, 'events.txt')
    settings['savefolder'] = savefolder
    settings['srcmdl'] = args['srcmdl']
    if not os.path.exists(settings['infile']):
        try:
            ph_files = [file for file in
                        os.listdir(datafolder) if 'PH' in file]
            with open(join(datafolder, 'events.txt'), 'wb') as evfile:
                for file in ph_files:
                    evfile.write('{} \n'.format(abspath(join(datafolder,
                                                             file))))
        except Exception:
            print('The events file could not be generated..\
                    check your data folder for consistency')

    settings['scfile'] = join(datafolder, 'spacecraft.fits')
    if not os.path.exists(settings['scfile']):
        try:
            sc_file = [file for file in os.listdir(datafolder) if 'SC' in file]
            move(join(datafolder, sc_file[0]), join(datafolder, 'spacecraft.fits'))
        except Exception:
            print('Problems with the Spacecaft File')

    settings['ltcube'] = settings['evfile'].split('.fits')[0] +\
        '_ltCube' + '.fits'
    settings['expmap'] = settings['evfile'].split('.fits')[0] +\
        '_expMap' + '.fits'
    if not os.path.isabs(settings['srcmdl']):
        settings['src_mdl_origin'] = join('..', 'models', settings['srcmdl'])
        settings['srcmdl'] = join(settings['savefolder'], settings['srcmdl'])
    else:
        settings['src_mdl_origin'] = settings['srcmdl']
        settings['srcmdl'] = join(settings['savefolder'], settings['srcmdl'].split('/')[-1])
    pos = get_src_pos(settings['src_mdl_origin'], settings['target_src'])
    settings['ra'] = float(pos['RA'])
    settings['dec'] = float(pos['DEC'])
    settings['emin'] = args['emin']
    settings['tmin'] = float(MJD_to_MET(args['time_range'][0]))
    settings['tmax'] = float(MJD_to_MET(args['time_range'][1]))

    return settings


def prepare_ana_files(settings):
    # Filter Events

    settings['evfile'] = join(settings['savefolder'], settings['evfile'])
    if not exists(settings['evfile']):
        filter_pars = ['evclass', 'evtype', 'zmax', 'rad', 'infile', 'emax',
                       'ra', 'dec', 'emin', 'tmin', 'tmax']
        for par in filter_pars:
            gt_app.filter[par] = settings[par]
        gt_app.filter['outfile'] = settings['evfile']
        gt_app.filter.run()
    else:
        print('{} already exists...skipping'.format(settings['evfile']))


    # MkTime
    if not exists(settings['evfile'].split('.fits')[0] + '_gti' + '.fits'):
        mktime_pars = ['filter', 'roicut', 'scfile', 'evfile']
        for par in mktime_pars:
            gt_app.maketime[par] = settings[par]
        settings['evfile'] = settings['evfile'].\
            split('.fits')[0] + '_gti' + '.fits'
        gt_app.maketime['outfile'] = settings['evfile']
        gt_app.maketime.run()
    else:
        print('{} already exists...skipping'.
              format(settings['evfile'].split('.fits')[0] + '_gti' + '.fits'))
        settings['evfile'] = settings['evfile'].\
            split('.fits')[0] + '_gti' + '.fits'


    # Exp Cube
    settings['ltcube'] = join(settings['savefolder'], settings['ltcube'])
    if not exists(settings['ltcube']):
        exp_Cube_pars = ['zmax', 'dcostheta', 'binsz', 'scfile', 'evfile']
        for par in exp_Cube_pars:
            gt_app.expCube[par] = settings[par]
        gt_app.expCube['outfile'] = settings['ltcube']
        gt_app.expCube.run()
    else:
        print('{} already exists...skipping'.format(settings['ltcube']))


    # Exp Map
    settings['expmap'] = join(settings['savefolder'], settings['expmap'])
    if not exists(settings['expmap']):
        exp_Map_pars = ['irfs', 'srcrad', 'nlong', 'nlat',
                        'nenergies', 'scfile', 'evfile']
        for par in exp_Map_pars:
            gt_app.expMap[par] = settings[par]
        gt_app.expMap['expcube'] = settings['ltcube']
        gt_app.expMap['outfile'] = settings['expmap']
        gt_app.expMap.run()
    else:
        print('{} already exists...skipping'.format(settings['expmap']))


    # Diffuse Response
    if not exists(settings['srcmdl']):
        copyfile(settings['src_mdl_origin'], settings['srcmdl'])
        diff_resp_pars = ['irfs', 'scfile', 'evfile', 'srcmdl']
        for par in diff_resp_pars:
            gt_app.diffResps[par] = settings[par]
        gt_app.diffResps.run()
    else:
        print('Diffuse Response already calculated...skipping')

    return settings
