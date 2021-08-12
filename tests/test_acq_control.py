# ------------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# ------------------------------------------------------------------------------
from __future__ import (division, print_function, absolute_import)


import unittest

from pyspectro.apps import UHSFFTS_32k, UHSFFTS_4k_complex
from pyspectro.applib.acq_control import AcquisitionControlInterface
from pyspectro.applib.processing import convert_raw_to_fs, convert_fs_to_dbfs

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")

from pyspectro.gui.mpl_figure import SpectrumFigure

import matplotlib.pyplot as plt
import numpy as np


def process_buffer(acqbuffer, sampleRate, complexData, numAverages,  voltageRange):
    logger.debug('Processing buffer')


    logger.debug('Released buffer lock')


class Test(unittest.TestCase):


    def setUp(self):

        self.resourceName = 'PXI4::4-0.0::INSTR'

        #self.ffts = UHSFFTS_32k(self.resourceName)
        self.ffts = UHSFFTS_4k_complex(self.resourceName)

        self.ffts.connect()

        self.ffts.instrument.Calibration.SelfCalibrate()

        self.ffts.numAverages = 1024

        self.acqControl = AcquisitionControlInterface(self.ffts) #:, notify = dataReadyCallback )

        self.ffts.downsample_ratio = 2

        self.Fs = self.ffts.sampleRate
        print('Fs={}'.format(self.Fs))

        self.specFig = SpectrumFigure(Nfft = 4096,
                                      sampleRate   =self.ffts.sampleRate,
                                      complexData  =self.ffts.app.complexData,
                                      numAverages  =self.ffts.numAverages,
                                      voltageRange =self.ffts.instrument.Channels['Channel1'].Range)
        plt.ion()
        plt.show()


        """ Test CW Generator """
        self.ffts._testMode = True
        self.ffts._testFreq = -100e6
        self.ffts.disablePolyphase = False

    def tearDown(self):

        self.acqControl.terminate()
        self.ffts.disconnect()

    def testSingle(self):

        #: Start acquisiton controller thread
        self.acqControl.initialize()

        self.acqControl.send_command('start')

        self.acqControl.dataReady.wait()

        with self.acqControl.buffer.lock:

            logger.debug('Acquired buffer lock')

            if self.acqControl.buffer.fftdata is not None:

                self.specFig.ydata = self.acqControl.buffer.fftdata
                self.specFig.redraw()
                plt.pause(1)
                plt.savefig('test_acq_control.png', bbox_inches='tight')


            else:
                logger.warning('Buffer empty')

        self.acqControl.dataReady.clear()


    @unittest.skip('temp')
    def testContinuous(self):
        """ Test continuous acquisiton with minimal data processing

        """
        #: Start acquisiton controller thread
        self.acqControl.initialize()

        self.ffts.continuousMode = True

        self.acqControl.send_command('start')

        period = self.ffts.Nfft * 1/ self.ffts.sampleRate * self.ffts.numAverages

        if self.ffts.app.complexData:
            nWordsPerMeasurement = self.ffts.Nfft
        else:
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
