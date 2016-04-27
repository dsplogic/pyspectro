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

import unittest

from pyspectro.drivers.Spectrometer import UHSFFTS_32k
from pyspectro.applib.connection import ConnectionManager

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")


class Test(unittest.TestCase):


    def setUp(self):

        self.resourceName = 'PXI4::4-0.0::INSTR'
        
        ffts = UHSFFTS_32k(self.resourceName)
        
        self.cm = ConnectionManager(ffts)
        

    def tearDown(self):
        
        self.cm = None
        
    def testConnectDisconnect(self):
        
        self.cm.initialize()
        
        self.cm.connect()
        
        print('Waiting for connection')
        self.cm.connected.wait()
        
        self.cm.disconnect()

        print('Waiting for disconnect')
        self.cm.disconnected.wait()
        
        self.cm.terminate()
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()