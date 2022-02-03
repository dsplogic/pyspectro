# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
# -----------------------------------------------------------------------------

import unittest

from pyspectro.apps import UHSFFTS_32k
from pyspectro.applib.connection import ConnectionManager
from pyspectro.applib.instrument_props import get_instrument_properties_string

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")


class Test(unittest.TestCase):


    def setUp(self):

        self.resourceName = 'PXI4::4-0.0::INSTR'
        
        self.ffts = UHSFFTS_32k(self.resourceName)
        
        self.cm = ConnectionManager(self.ffts)
        

    def tearDown(self):
        
        self.cm = None
        
    def testConnectDisconnect(self):
        
        self.cm.initialize()
        
        self.cm.connect()
        
        logger.info('Waiting for connection')
        self.cm.connected.wait()
        
        with self.ffts.lock:
            deviceinfo = get_instrument_properties_string(self.ffts)
            logger.info(deviceinfo)
            
        print('Interleaving status: {}'.format(self.ffts.interleaving))
        
        print('Current sample rate: {}'.format(self.ffts.instrument.Acquisition.SampleRate))
            
        self.cm.disconnect()

        logger.info('Waiting for disconnect')
        self.cm.disconnected.wait()
        
        self.cm.terminate()
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()