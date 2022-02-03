# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
# -----------------------------------------------------------------------------


from configparser import ConfigParser
import os
import logging
logger = logging.getLogger(__name__)


FNAME   = 'pyspectro.lic'
HOME    = os.path.expanduser('~')
licfile = os.path.join(HOME, FNAME)


def read_license_keys(serial_no):
    """ Read SpectroCore License keys from file

    This function reads a properly formatted license file and returns
    the license keys for the given instrument serial number. 
    
    Inputs
    ------
    
    serial_no : str
        Instrument Serial Number, e.g. 'MY00010001'  
        
    Returns
    ------
    
    result : 3-tuple
    
        (keys, err, licfile)
    
        keys : dict
            Dictionary of license keys.
            
        err: str
            If an error occurs, a non-empty string is returned with
            a description of the error.  If no error occurs, an 
            empty string is returned.
    
        licfile : str
            Filename of the license file that was checked.  

    License File Format
    -------------------
    
        The license file must be named 'pyspectro.lic' and located
        in the user's home directory.
        
        The license file uses the standard ConfigParser module file format
        where the name of each section is the instrument serial number.
        This allows a single license file to support multiple instrument
        licenses.
        
        Each section (e.g. device) contains 4 items, labeled 'key0', 'key1'
        'key2', and 'key3', representing the 4 license key values.
    
        Each key value is an 8-digit hexadecimal number and must be preceded
        by the string '0x'.

        Example $HOME/pyspectro.ini file contents containing license keys for
        two instruments:
        
            [MY00010001]
            key0 = 0x01234567
            key1 = 0x89ABCDEF
            key2 = 0x01234567
            key3 = 0x89ABCDEF
    
            [MY00010002]
            key0 = 0x89ABCDEF
            key1 = 0x89ABCDEF
            key2 = 0x89ABCDEF
            key3 = 0x89ABCDEF
    
    """
    
    #: Default return parameters
    keys = {}
    err = ''

    #: Open License file and get parser object
    parser = ConfigParser()
    flist = parser.read(licfile);
    logger.info('License file found %s' % licfile)
    if len(flist) != 1:    
        err = 'License file not found %s' % licfile
        logger.info(err)
        return keys, err, licfile

    #: Verify that serial number in license file        
    if serial_no not in parser.sections():
        err = 'License for %s not found in License file %s' % (serial_no, licfile)
        return keys, err, licfile
        
    #: Get License Keys
    keys = dict(parser.items(serial_no))

    #: Return key dictionary    
    return keys, err, licfile
    
if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG, format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")
    
    keys, err, licfile = read_license_keys('MY00090571')
    print(keys)
    print(err)
    print(licfile)    