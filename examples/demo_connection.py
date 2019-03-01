#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------
from __future__ import (division, print_function, absolute_import)

""" Instrument Connection Example (not threaded)

This example demonstrates how to performing the following tasks using
the threeaded ConnectionManager object:

    - Connect to the instrument
    - Read basic properties from the instrument 
    - Disconnect from the instrument

"""

from pyspectro.drivers.Spectrometer import UHSFFTS_32k
from pyspectro.applib.instrument_props import get_instrument_properties_string

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")


#: Define the resource identifier used to connect
resourceName = 'PXI4::4-0.0::INSTR'

#: Instantiate the driver 
ffts = UHSFFTS_32k(resourceName)

#: Create a connection manager object and connect
ffts.connect()

#: Get device information
deviceinfo = get_instrument_properties_string(ffts)
logger.info(deviceinfo)

#: Disconnect        
ffts.disconnect()

