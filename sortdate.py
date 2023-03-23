#!/usr/bin/env python

__author__ = "Andrea Gangemi"
__copyright__ = "Copyright 2023, " + __author__
__credits__ = [""]
__license__ = "GPL"
__version__ = "1.3"
__maintainer__ = "Andrea Gangemi"
__email__ = "andrea.gangemi@gmail.com"
__url__ = "https://about.me/andrea.gangemi"
__status__ = "Production"

import os
import os.path

import shutil
from optparse import OptionParser

import exifread
from geopy.geocoders import Nominatim

# data_dir = "."
VERBOSE = False
MOVEFILES = True

DATE_TAG = 'EXIF DateTimeOriginal'


def verboseprint(s):
    if VERBOSE:
        print(s)


def get_gps_location(tags):

    latitude = tags.get('GPS GPSLatitude').printable
    latituderef = tags.get('GPS GPSLatitudeRef').printable
    longitude = tags.get('GPS GPSLongitude').printable
    longituderef = tags.get('GPS GPSLongitudeRef').printable

    # convert coordinate in 2 float values
    # with some tweaks to get rid of spurious characters in strings

    latitude_deg = float(latitude.split(',')[0][1:])
    latitude_min = float(latitude.split(',')[1])
    latitude_sec = float(eval(latitude.split(',')[2][:-1]))
    latitude_dec = latitude_deg + (latitude_min / 60.0) + (latitude_sec / 3600.0)
    if latituderef == 'S':
        latitude_dec = -latitude_dec

    longitude_deg = float(longitude.split(',')[0][1:])
    longitude_min = float(longitude.split(',')[1])
    longitude_sec = float(eval(longitude.split(',')[2][:-1]))
    longitude_dec = longitude_deg + (longitude_min / 60.0) + (longitude_sec / 3600.0)
    if longituderef == 'W':
        longitude_dec = -longitude_dec

    # Format the GPS location string
    location = f"{latitude_dec:.6f}, {longitude_dec:.6f}"

    # Note Nominating is slow and shoul request maximum 1 request per second
    geoloc = Nominatim(user_agent="GetLoc", timeout=200)

    # passing the coordinates
    locname = geoloc.reverse(location, language='en')

    loc_dict = locname.raw
    place = loc_dict['address']['city']

    print(place)
    return place


def createdirname(stringdate, stringgps='', separator='_', destdir='.'):
    dirname = None
    if stringdate:
        dirname = destdir + '/' + stringdate[:4] + stringdate[5:7] + stringdate[8:10] + separator + stringgps
    return dirname


def makedir(dirname):
    created = False
    if os.path.exists(dirname) and os.path.isdir(dirname):
        pass
    else:
        os.mkdir(dirname)
        created = True
    return created


def processfiles(imglist, options):
    print(type(imglist))
    dircounter = 0
    filemoved = 0
    datefound = False
    for filename in imglist:
        verboseprint(' now processing: %s' % filename)

        with open(filename, 'rb') as image_file:
            img_tags = exifread.process_file(image_file)
        if img_tags:
            # verboseprint(img_tags.keys())
            try:
                if DATE_TAG in img_tags.keys():
                    datefound = True
                    stringdate = str(img_tags[DATE_TAG])
                    verboseprint('Date and time taken: ' + stringdate)

                    stringgps = ''
                    if options.usegeo:
                        stringgps = get_gps_location(img_tags)
                    dirname = createdirname(stringdate, stringgps, destdir=options.dest_dir)

                    created = makedir(dirname)
                    if created:
                        dircounter = dircounter + 1
                    moved = copymovefile(filename, dirname)
                    filemoved = filemoved + moved
            finally:
                pass

        if datefound:
            verboseprint("FOUND")
        else:
            verboseprint(' EXIF DateTime not found, skipping.')

    verboseprint(' Done! ')
    verboseprint(' ' + str(dircounter) + ' Directories created ')
    tmpstring = 'copied'
    if MOVEFILES:
        tmpstring = 'moved'
    verboseprint(' ' + str(filemoved) + ' of ' + str(len(imglist)) + ' Files ' + tmpstring + '.')
    return dircounter


def copymovefile(fullfilename, pathname):
    moved = 0
    counter = 0

    filename = str(fullfilename).rpartition('/')[-1]
    newfilename = filename

    print(pathname)
    while os.path.exists(pathname + '/' + newfilename) and counter <= 999:
        newfilename = filename
        print('filename: ' + newfilename)
        counter = counter + 1
        newfilename = ('%03d' % counter) + '_' + newfilename
        print(newfilename)
    if counter <= 999:
        if MOVEFILES:
            shutil.move(fullfilename, pathname + '/' + newfilename)
        else:
            shutil.copy2(fullfilename, pathname + '/' + newfilename)
        moved = 1
    else:
        verboseprint("too many copies, file skipped")
    return moved


def main():
    global VERBOSE
    global MOVEFILES

    usage = "usage: %prog [options] root_directory"
    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose",
                      action="store_true",
                      dest="verbose",
                      default=True,
                      help="verbose mode ON [default]")
    parser.add_option("-q", "--quiet",
                      action="store_false",
                      dest="verbose",
                      help="run silent")
    parser.add_option("-d", "--dest-dir",
                      action="store",
                      dest="dest_dir",
                      default=".",
                      help="data directory [current]")
    parser.add_option("-s", "--source-dir",
                      action="store",
                      dest="source_dir",
                      default=".",
                      help="data directory [current]")
    parser.add_option("-m", "--move",
                      action="store_true",
                      dest="movefiles",
                      default=True,
                      help="move files")
    parser.add_option("-c", "--copy",
                      action="store_false",
                      dest="movefiles",
                      default=True,
                      help="copy files")
    parser.add_option("-g", "--geo",
                      action="store_true",
                      dest="usegeo",
                      default=False,
                      help="Try to figure out GPS location (Slow!)")

    (options, args) = parser.parse_args()

    VERBOSE = options.verbose
    MOVEFILES = options.movefiles

    verboseprint(' \nHi, this is SortDate ' + __version__ + ' 8-)')
    verboseprint(' Written by ' + __author__ + ': ' + __url__)
    verboseprint(' ')
    verboseprint(' REMEMBER: SortDate COMES WITHOUT WARRANTY OF ANY KIND ')
    verboseprint(' ')
    verboseprint(' I\'m going to create dirs by looking inside EXIF tags stored in your pictures')

    start_dir = os.getcwd()
    os.chdir(options.dest_dir)
    filelist = [(options.source_dir + '/' + x) for x in os.listdir(options.source_dir) if
                os.path.isfile(options.source_dir + '/' + x)]
    print(options.dest_dir, filelist)
    processfiles(filelist, options)
    os.chdir(start_dir)
    return


if __name__ == "__main__":
    main()
