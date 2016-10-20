#------------------------------------------------------------------------------
# Copyright (c) 2016, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------
from __future__ import (division, print_function, absolute_import)

""" Demonstrate reading HDF5 acquisition format

This program demonstrates:

    - Reading recorded instrument data from a HDF5 log file

"""

import os, logging
from Tkinter import Tk
from tkFileDialog import askopenfilename
from pyspectro.applib.datalogger import SpectrumDataReader
from plot_helpers import plot_raw_data

#: Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(threadName)10s %(levelname)-8s %(message)-60s  <%(name)-15s>")

""" Ask user to select HDF5 file """
HOME      = os.path.expanduser('~')  #: Get user home directory
PYHOME    = os.path.abspath(os.path.join(HOME, 'pyspectro'))
Tk().withdraw() 
options = {'initialdir' : PYHOME, 
           'filetypes': [('HDF5 Files', '*.hdf5'),('all files', '.*')]}
filename = askopenfilename( **options ) 

#: Create HDF5 reader object
rdr = SpectrumDataReader(filename)

#: Number of acquisitons in file
logger.info('Found %s acquisitions' % len(rdr.acquisitions))

#: Inspect first acquisition            
acq1 = rdr.acquisitions[0]
logger.info('Acquisiton ID: %s' % acq1['name'])         
logger.info('Number of measurements: %s' % acq1['msrmnt_count'])

#: Plot results of *first* measurement in acquisiton
rawfftdata = rawdata = acq1['fftdata'][0]         
numAverages = acq1['num_averages'][0]
msrmnt_idx = acq1['msrmnt_idx'][0] #: This value can be used to detect "dropped" measurement recordings
logger.info('Plotting measurement %s' % msrmnt_idx)
plot_raw_data(rawfftdata, numAverages)


