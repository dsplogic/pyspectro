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

"""
Description: Spectrometer Driver

This module contains the python driver for the 
1 GHz UHSFFTS Spectrometer with 16k channels.
It may be used directly or referred to as a model
for drivers written in other languages.   

Copyright DSPlogic 2016

"""
              

#: Package imports
from atom.api import Int, Bool, Property, Float        
import time    
import numpy as np
from .dsplogic import BUFFER_ID
from ..common.bitreversal import bitrevorder
from ..common.bitmanipulation import testBit, setBit, clearBit
from .AgMD2Digitizer import KeysightDigitizer


""" Driver register map

"""
REGISTER_MAP = {
    'main_control' : 0x3300,
    'main_status'  : 0x3304,
    'num_average'  : 0x3308,
    'msrmnt_cnt'   : 0x330C,
    'overflow'     : 0x3310,
    '_tg_control1' : 0x3314,
    '_tg_control2' : 0x3318,
    '_reserved1'   : 0x331C,
    '_tg_ph0'      : 0x3320,
    '_tg_ph1'      : 0x3324,
    '_tg_ph2'      : 0x3328,
    '_tg_ph3'      : 0x332C,
    '_tg_ph4'      : 0x3330,
    '_tg_ph5'      : 0x3334,
    '_tg_ph6'      : 0x3338,
    '_tg_ph7'      : 0x333c
}



class Spectrometer(KeysightDigitizer):
    """ Spectrometer driver

    Properties
    ----------
    
    numAverages : int
        Number of averages to accumulate.  
        The input can range from 2 to 1,000,000 (approximately 16 seconds)
        
    continuousMode: bool
        When false, the spectrometer is in one-shot mode.  It will perform the
        requested number of accumulations and return the result.
        When true, the spectrometer is in continuous mode.  It will continue
        writing measurement to memory at the end of each accumulation period.

    measurementCount : int
        The number of measurements that have been performed since the 
        start of acquisition. In one-shot mode, measurementCount will be 
        incremented to 1 after numAverages accumulations have been
        performed and the resulting measurement has been written to memory.
        In continuous mode, the measurementCount will continue to increment
        until a stopAcquisiton command is received.
        
    measurementComplete : bool
        During one-shot acquisition, this property indicates that the measurement
        has been completed and the result is ready in DDR memory

    overflow : int
        A non-zero value indicates that a signal overflow error occurred internal
        to the DSP core.
        
    memoryError: int
        A non-zero value indicates that a DDR memory conflict has occurred between
        the software and the DSP core. 
    
    """

    #: FFT Length
    Nfft = Int()

    #: Number of averages (R/W)
    numAverages = Property()
    
    #: Set continuous mode vs. one-shot (R/W)
    continuousMode = Property()

    #: Set continuous mode vs. one-shot (R/W)
    disablePolyphase = Property()
    
    #: Current measurement count (Read-Only)
    measurementCount = property(lambda self: self.read_register('msrmnt_cnt')) 

    #: Current measurement count (Read-Only)
    overflow = property(lambda self: self.read_register('overflow')) 

    #: An memory error
    memoryError = Property()
    
    
    #: PRIVATE PROPERTIES
    #:-------------------
    
    #: Floating-point enabled dsp core (private)
    _float = Bool(False)
    
    #: Number of frequency bins (private)
    _nFreqs = Int()
    
    #: Test mode for internal use
    _testMode   = Property()
    __testMode = Bool()
    
    #: Test frequency
    _testFreq  = Property()
    __testFreq = Float()
    
    def __init__(self, resourceName, **kwargs):
        """ Initialize spectrometer driver
        
        Delegate initialization to superclass (KeysightDigitizer)
        Turn on interleaving
        """

        super(Spectrometer, self).__init__(resourceName=resourceName, **kwargs)
        
        self.interleaving = True
        
        self._nFreqs = self.Nfft//2
        
    def read_register(self, reg):
        """ Read control register
        
        Parameters
        ----------
        reg : str
            Name of register in REGISTER_MAP
        
        """
        
        if reg in REGISTER_MAP.iterkeys():
            reg_addr = REGISTER_MAP[reg]
            return self.logicDevice['DpuA'].ReadRegisterInt32(reg_addr)
        else:
            raise Exception('Invalid register %s' % reg)
    
    def write_register(self, reg, val):
        """ Write control register
        
        Parameters
        ----------
        reg : str
            Name of register in REGISTER_MAP
        val : Int32
            32-bit register value
        
        """
        if reg in REGISTER_MAP.iterkeys():
            reg_addr = REGISTER_MAP[reg]
            self.logicDevice['DpuA'].WriteRegisterInt32(reg_addr, val)

        else:
            raise Exception('Invalid register %s' % reg)

    def read_memory(self, chan):
        """ Read digitizer memory

        When channels are interleaved, processing results may be contained in
        one or both channels. 
        
        Parameters
        ----------
        chan : int
            Set to 1 to read channel 1 memory (from DDR A)
            Set to 2 to read channel 2 memory (from DDR B)
            
        Returns
        -------
        result : np.array(dtype=float32) 
            Processing results contained in DDR memory
        
        """

        #with self.lock:

        nbrint32 = self._nFreqs//2
        
        if chan == 1:
            
            self.memoryBank['DpuA']['DDR3A'].AccessMode = 1 # DDRA in read mode
            buff = BUFFER_ID['DpuA.DDR3A']
            data_int32 = self.logicDevice['DpuA'].ReadIndirectInt32(buff, 0x0, nbrint32)
            self.memoryBank['DpuA']['DDR3A'].AccessMode = 0 
        
        elif chan == 2:
        
            self.memoryBank['DpuA']['DDR3B'].AccessMode = 1 # DDRA in read mode
            buff = BUFFER_ID['DpuA.DDR3B']
            data_int32 = self.logicDevice['DpuA'].ReadIndirectInt32(buff, 0x0, nbrint32)
            self.memoryBank['DpuA']['DDR3B'].AccessMode = 0 
        
        else:
        
            raise Exception('Invalid Channel ID')
            
        FirstValidPoint = data_int32[2]
        ActualPoints    = data_int32[1]

        result      = np.array(data_int32[0][FirstValidPoint : FirstValidPoint + ActualPoints ],
                               dtype = np.uint32)

        if self._float:
            result = result.view('float32')
                    
        return result


    def _get_numAverages(self):
        return self.read_register('num_average') + 1

    def _set_numAverages(self, val):
        #with self.lock:
        self.write_register('num_average', val-1)
    
    def _get_continuousMode(self):
        
        mcreg = self.read_register('main_control')

        return testBit(mcreg, 0)
        
    def _set_continuousMode(self, val):

        #with self.lock:
        
        mcreg = self.read_register('main_control')
        
        if val:
            mcreg = setBit(mcreg, 0)
        else:
            mcreg = clearBit(mcreg, 0)
            
        self.write_register('main_control', mcreg)
            
    def _get_disablePolyphase(self):
        
        mcreg = self.read_register('main_control')

        return testBit(mcreg, 1)
        
    def _set_disablePolyphase(self, val):

        #with self.lock:
        
        mcreg = self.read_register('main_control')
        
        if val:
            mcreg = setBit(mcreg, 1)
        else:
            mcreg = clearBit(mcreg, 1)
            
        self.write_register('main_control', mcreg)

    def _get__testMode(self):
        
        mcreg = self.read_register('_tg_control1')

        return testBit(mcreg, 0)

    def _set__testMode(self, val):
        
        #with self.lock:
            
        mcreg = self.read_register('_tg_control1')
        
        if val:
            mcreg = setBit(mcreg, 0)
            self.__testMode = True
        else:
            mcreg = clearBit(mcreg, 0)
            self.__testMode = False
            
        self.write_register('_tg_control1', mcreg)
        
    def _get__testFreq(self):
        
        return self.__testFreq
        
        #phst = self.read_register('_tg_control2')
        #return float(phst) * 250000000.0/(2**24)
        
    def _set__testFreq(self, f):

        if f > 1e9:
            raise Exception('Frequency must be less than 1 GHz')

        #with self.lock:    
                
        phst = int( float(f)/2e9 * (2**28))
        
        self.write_register('_tg_ph0',      0 * phst)
        self.write_register('_tg_ph1',      1 * phst)
        self.write_register('_tg_ph2',      2 * phst)
        self.write_register('_tg_ph3',      3 * phst)
        self.write_register('_tg_ph4',      4 * phst)
        self.write_register('_tg_ph5',      5 * phst)
        self.write_register('_tg_ph6',      6 * phst)
        self.write_register('_tg_ph7',      7 * phst)
        self.write_register('_tg_control2', 8 * phst)

        self.__testFreq = float(phst) / (2**28) * 2e9 
        
        if self.__testMode:
            mcreg = self.read_register('_tg_control1')
            mcreg = clearBit(mcreg, 0)
            mcreg = setBit(mcreg, 0)
                
    
    def _get_memoryError(self):
        reg = self.read_register('main_status')
        return reg & 0x000000ff
        

    """ Addtional status
    
    """ 
    def _fpgaCanAccessMemory(self):
        reg = self.read_register('main_status')
        return reg & 0x01000000
    
    def _fpgaCoreIsActive(self):
        #: As determined by mem_active
        reg = self.read_register('main_status')
        return reg & 0x04000000

        

""" Top level spectrometer classes for user instantiation

"""
def UHSFFTS_32k(resourceName=''):
    
    bitfile = 'U5303ADPULX2FDK_uhsffts_32k_float_0_2_16.bit'
    
    return Spectrometer(resourceName, bitfile=bitfile, _float=True, Nfft = 32768)
         
def UHSFFTS_32k_fxp(resourceName=''):
    
    bitfile = 'U5303ADPULX2FDK_uhsffts_32k_fixed_0_1_35.bit'
    
    return Spectrometer(resourceName, bitfile, _float=False, Nfft = 32768)
        

if __name__ == "__main__":


    pass
    
        