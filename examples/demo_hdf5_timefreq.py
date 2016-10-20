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

""" Demonstrate time/frequency plot using HDF5 acquisition format

This program demonstrates:

    - Reading recorded instrument data from a HDF5 log file
    - Surface contour of time vs frequency

"""

import os, logging
from pyspectro.applib.datalogger import SpectrumDataReader
from plot_helpers import plot_raw_data, plot_waterfall

#: Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(threadName)10s %(levelname)-8s %(message)-60s  <%(name)-15s>")

""" Ask user to select HDF5 file """
filename = './data/acq_data_100_measurements.hdf5' 

#: Create HDF5 reader object
rdr = SpectrumDataReader(filename)

#: Number of acquisitons in file
logger.info('Found %s acquisitions' % len(rdr.acquisitions))

#: Inspect first acquisition            
acq1 = rdr.acquisitions[0]
logger.info('Acquisiton ID: %s' % acq1['name'])         
logger.info('Number of measurements: %s' % acq1['msrmnt_count'])

#: Plot results of *first* measurement in acquisiton
rawfftdata  = acq1['fftdata']         
numAverages = acq1['num_averages']
msrmnt_idx  = acq1['msrmnt_idx'] #: This value can be used to detect "dropped" measurement recordings

logger.info('Plotting measurement %s' % msrmnt_idx[0])
plot_raw_data(rawfftdata[0], numAverages[0])
plot_waterfall(rawfftdata , numAverages, msrmnt_idx )

