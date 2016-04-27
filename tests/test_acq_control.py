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
from pyspectro.applib.acq_control import AcquisitionControlInterface
from pyspectro.applib.processing import convert_raw_to_fs, convert_fs_to_dbfs

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")

import matplotlib.pyplot as plt
import numpy as np


def plotresult(dBspectrum, Fs):    
    #: Compute frequency axis
    Nfft = 2*dBspectrum.size
    
    f = np.arange(Nfft/2, dtype=np.float )
    df = Fs / 2.0 / Nfft/2
    f = f * df
    
    #: Plot data
    fig = plt.figure()
    
    plt.xlabel("Frequency")
    plt.ylabel("Power")
    plt.grid(True)
    axes = plt.gca()
    axes.set_ylim([-120, 0])
    plt.plot(f, dBspectrum)
    
    plt.savefig('test_acq_control.png', bbox_inches='tight')
    


def process_buffer(acqbuffer):
    logger.debug('Processing buffer')
    
    with acqbuffer.lock:
        logger.debug('Acquired buffer lock')
        
        if acqbuffer.fftdata is not None:
            
            fft_fs = convert_raw_to_fs(acqbuffer.fftdata, acqbuffer.numAverages)
            
            fft_dbfs = convert_fs_to_dbfs(fft_fs)
            
            plotresult(fft_dbfs, 2.0e9)
            
        else:
            logger.warning('Buffer empty')
    
    logger.debug('Released buffer lock')


class Test(unittest.TestCase):


    def setUp(self):

        self.resourceName = 'PXI4::4-0.0::INSTR'
        
        self.ffts = UHSFFTS_32k(self.resourceName)
        self.ffts.connect()
        
        self.ffts.instrument.Calibration.SelfCalibrate()

        self.acqControl = AcquisitionControlInterface(self.ffts) #:, notify = dataReadyCallback )

        self.Fs = self.ffts.instrument.Acquisition.SampleRate

    def tearDown(self):
        self.acqControl.terminate()
        self.ffts.disconnect()

    def testSingle(self):


        self.ffts.numAverages = 1024
    
        #: Start acquisiton controller thread
        self.acqControl.initialize()
        
        self.acqControl.send_command('start')
        
        self.acqControl.dataReady.wait()

        process_buffer(self.acqControl.buffer)
        
    def testContinuous(self):
        numAverages = 256

        self.ffts.numAverages = numAverages
    
        #: Start acquisiton controller thread
        self.acqControl.initialize()

        self.ffts.continuousMode = True
        
        self.acqControl.send_command('start')
 
        period = self.ffts.Nfft * 1/2.0e9 * numAverages
        nWordsPerMeasurement = self.ffts.Nfft/2
        bytesPerWord = 4
        bytesPerSecond = nWordsPerMeasurement / period * bytesPerWord
        
        logger.info('Required throughput: %s bytes/sec' % bytesPerSecond)

        #: Wait for N acquisitions
        for k in range(500):
 
            self.acqControl.dataReady.wait()
            self.acqControl.dataReady.clear()
            
        self.acqControl.send_command('stop')
        from pyspectro.common.atom_helpers import prettyMembers
        
        logger.debug(prettyMembers(self.acqControl.buffer.stats))        

        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()