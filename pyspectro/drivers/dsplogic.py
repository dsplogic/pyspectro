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



from atom.api import Str, Int, Bool, Float
import time
import numpy as np

from .AgMD2Digitizer import KeysightDigitizer, AcquisitionMode, InputCoupling

""" Buffer IDs

This 64 GB address space is accessible from the host computer over PCIe through an address indirection mechanism: 

Each memory is assigned a Buffer ID. 
    By setting the Buffer ID in the PCIe interface a window with AXI4-Full base address and high address corresponding 
    to the selected memory area is opened, then memory can be accessed through Programmed I/O or DMA.
    
    Buffer IDs 0..15 are reserved for the Keysight region. 
    Buffer IDs 16..31 are available for the FDK User

The user core FPGA code defines the following
"""
BUFFER_ID  = {'DpuA.QDR2' : 20,
              'DpuA.DDR3A': 28,
              'DpuA.DDR3B': 30
               }



class U5303A(KeysightDigitizer):
    
    pass




        
        


        
            
        #: Set Memory Banks to FIFO Mode 
        #: *** Experimental - little documentation ***
        #: This command fails if the update_settings() method is not called first. 
        #self.MemoryBanks['DpuA']['DDR3A'].FIFOModeEnabled = True
        #self.MemoryBanks['DpuA']['DDR3B'].FIFOModeEnabled = True
        
        #: TBD: Do we need to call this after setting FIFOModeEnabled?
        #self._instr.Acquisition.ApplySetup() 
    
        # def _set_interleaving(self, newState):
        #     
        #     currentState = self.interleaving
        #     
        #     if newState == currentState: #: Nothing to do
        #         return
        #     
        #     if newState:
        #         self._interleaving = True
        #         
        #     else:
        #         self._interleaving = False
        #         
        #     # TBD Change Sample RATE??
        #         
        # def _get_interleaving(self):
        #     
        #     return self._interleaving

 
            


