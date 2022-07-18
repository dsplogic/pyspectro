# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# -----------------------------------------------------------------------------

import logging
import unittest

import numpy as np

from pyspectro.applib.acq_control import AcquisitionControlInterface
from pyspectro.apps import UHSFFTS_32k
from pyspectro.apps import UHSFFTS_4k_complex

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")

from pyspectro.gui.mpl_figure import SpectrumFigure

import matplotlib.pyplot as plt


class Test(unittest.TestCase):
    def setUp(self):

        self.resourceName = "PXI4::4-0.0::INSTR"

        # self.ffts = UHSFFTS_32k(self.resourceName)
        self.ffts = UHSFFTS_4k_complex(self.resourceName)

        self.ffts.connect()

        self.ffts.instrument.Calibration.SelfCalibrate()

        self.ffts.numAverages = 8192

        self.acqControl = AcquisitionControlInterface(self.ffts)

        self.ffts.downsample_ratio = 1

        self.Fs = self.ffts.sampleRate
        print("Fs={}".format(self.Fs))

        self.specFig = SpectrumFigure(
            Nfft=self.ffts.Nfft,
            sampleRate=self.ffts.sampleRate,
            complexData=self.ffts.app.complexData,
            numAverages=self.ffts.numAverages,
            voltageRange=self.ffts.instrument.Channels["Channel1"].Range,
        )

        """ Test Digital CW Generator """
        self.ffts._testMode = True
        self.ffts._testFreq = 100e6
        self.ffts.disablePolyphase = False

    def tearDown(self):

        self.acqControl.terminate()
        self.ffts.disconnect()

    def testSingle(self):

        #: Start acquisition controller thread
        self.acqControl.initialize()

        self.acqControl.send_command("start")

        self.acqControl.dataReady.wait()

        with self.acqControl.buffer.lock:

            logger.debug("Acquired buffer lock")

            if self.acqControl.buffer.fftdata is not None:

                self.specFig.ydata = self.acqControl.buffer.fftdata
                self.specFig.redraw()
                plt.ion()
                plt.show()

                plt.pause(1)
                plt.savefig("test_acq_control.png", bbox_inches="tight")

            else:
                logger.warning("Buffer empty")

        self.acqControl.dataReady.clear()

    def testContinuous(self):
        """Test continuous acquisiton with minimal data processing"""
        #: Start acquisition controller thread
        self.acqControl.initialize()

        self.ffts.continuousMode = True

        self.acqControl.send_command("start")

        period = self.ffts.Nfft * 1 / self.ffts.sampleRate * self.ffts.numAverages
        logger.info('Measurement period: {}'.format(period))

        if self.ffts.app.complexData:
            nWordsPerMeasurement = self.ffts.Nfft
        else:
            nWordsPerMeasurement = self.ffts.Nfft / 2

        bytesPerWord = 4
        bytesPerSecond = nWordsPerMeasurement / period * bytesPerWord

        logger.info("Required throughput: %s bytes/sec" % bytesPerSecond)

        freq_step = self.ffts.sampleRate / self.ffts.Nfft
        freq_init = -self.ffts.sampleRate / 2


        #: Process 10 sequential measurements
        for k in range(10):

            # Wait for data to be ready
            self.acqControl.dataReady.wait()

            # Acquire buffer lock
            with self.acqControl.buffer.lock:

                if self.acqControl.buffer.fftdata is not None:

                    # Read data from buffer
                    fftdata = self.acqControl.buffer.fftdata

                    # Perform some basic processing (get max value)
                    max_value = np.amax(fftdata)
                    max_idx = np.argmax(fftdata)
                    max_freq = freq_init + freq_step * max_idx
                    logger.info("Max value: {} @ freq {} MHz".format(max_value, max_freq/1.0e6))

                else:
                    logger.warning("Buffer empty")

            # Clear data ready flag
            self.acqControl.dataReady.clear()

        self.acqControl.send_command("stop")
        from pyspectro.common.atom_helpers import prettyMembers

        logger.debug(prettyMembers(self.acqControl.buffer.stats))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
