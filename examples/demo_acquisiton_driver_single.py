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
""" Single acquisiton example using only the Spectrometer Driver

This example demonstrates usage of the Spectrometer Driver to perform
a single acquisiton.

"""

import logging
from plot_helpers import plot_raw_data
from pyspectro.drivers.Spectrometer import UHSFFTS_32k, MemoryConverter

#: Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(threadName)10s %(levelname)-8s %(message)-60s  <%(name)-15s>")

#: Instrument ID
resourceName = 'PXI4::4-0.0::INSTR'

#: Instantiate the instrument driver
ffts = UHSFFTS_32k(resourceName)

#: Request a connection to the device
ffts.connect()

#: Configure device for a single acquistion
ffts.numAverages = 1024
ffts.continuousMode = False  #: False for a single acquisiton

#: Start a signle
#: Note that the first acquisiton may take extra time if a calibration is required.
ffts.startProcessing()

#: Wait for measurement count to increment
while ffts.measurementCount < 1:
    pass

#: Stop Processing
ffts.stopProcessing()

#: Read data from memory
data_ddra    = ffts.read_memory(1)
data_ddrb    = ffts.read_memory(2)

#: Convert data into FFT format        
rawfftdata = MemoryConverter(ffts.Nfft).process(data_ddra, data_ddrb)

#: Plot result        
plot_raw_data(rawfftdata, ffts.numAverages)







