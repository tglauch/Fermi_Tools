import os
from os.path import exists, join, abspath
import gt_apps as gt_app
from shutil import copyfile
import configparser
from ast import literal_eval
import xml.etree.ElementTree as ET


def MJD_to_MET(mjd_time):
    MJDREF = 51910.0 + 7.428703703703703E-4
    return (mjd_time - MJDREF) * 86400.


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

    savefolder = join('.', args['bpath'],
                  '{}_{}'.format(args['time_range'][0],
                                 args['time_range'][1]),
                  str(int(args['emin'])))

    if not exists(savefolder):
        print('Create Folder in {}'.format(savefolder))
        os.makedirs(savefolder)

    config = configparser.ConfigParser()
    config.read(join('.', args['bpath'], args['config']))
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
    settings['src_mdl_origin'] = join('.', args['bpath'], settings['srcmdl'])
    settings['srcmdl'] = join(settings['savefolder'], settings['srcmdl'])
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
