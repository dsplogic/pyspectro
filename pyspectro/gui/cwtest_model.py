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



from atom.api import Atom, Bool, Float, Typed, observe
from pyspectro.drivers.Spectrometer import Spectrometer


class CwTestModel(Atom):

    device = Typed(Spectrometer)
    
    #: Test settings
    testMode = Bool()
    #testFreq = Float()

    def __init__(self, device):
        """ Initialize 
        
        """
        self.device = device


    @observe('testMode')
    def _testModeHandler(self, change):
        with self.device.lock:
            if change['value']:
                self.device._testMode = True
            else:
                self.device._testMode = False

    def applyTestFreq(self, value):
        with self.device.lock:
            self.device._testFreq = value #:self.testFreq
        
#     @observe('testFreq')
#     def _testFreqHandler(self, change):
#         
#         self.device._testFreq = change['value']

    # def destroy(self):
    #     """ A reimplemented destructor.
    # 
    #     """
    #     super(DeviceParameterModel, self).destroy()
    #     del self.comif
