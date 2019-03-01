#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------

""" Single acquisiton example using PySpectroCore multi-threaded application

This example demonstrates usage of the PySpectroCore Application
to perform a single data acquisition.

"""

import logging
from pyspectro.applib.core import PySpectroCore


#: Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(threadName)10s %(levelname)-8s %(message)-60s  <%(name)-15s>")


#: Instrument ID
resourceName = 'PXI4::4-0.0::INSTR'

#: Start applciation
core = PySpectroCore()

#: Assign a simple function to the "on_state_change" callback.
#: This callback allows user code to be executed on the main application loop thread
#: whenever the state changes.
core.on_state_change= lambda state: logger.debug('state changed to {0}'.format(state))

#: Request a connection to the device
core.connect(resourceName)

#: Wait for the connection (or perform other processing)
logger.debug('Waiting for connection')
if not core.connect_event.wait(10.0):
    logger.debug('Connect failed')
logger.debug('Connection completed')

#: Configure instrument parameters
#: For thread safety, the lock must always be obtained before accessing the instrument
with core.device.lock:
    core.device.numAverages = 1024
    core.device.continuousMode = False  #: False for a single acquisiton

#: Start a signle
#: Note that the first acquisiton may take extra time if a calibration is required.
core.start()

#: Wait for stop_event, which will be asserted when the acquisiton is complete, then clear it.
core.stop_event.wait()
core.stop_event.clear()

#: Disconnect from device
logger.debug('Disconnecting')
core.disconnect()
core.disconnect_event.wait()

#: Terminate core application 
core.terminate()

