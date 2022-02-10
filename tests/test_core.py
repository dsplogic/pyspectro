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

from pyspectro.applib.core import PySpectroCore

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(relativeCreated)5d %(threadName)10s %(levelname)-8s %(message)-60s  <%(name)-15s>"
)

import time

resourceName = "PXI4::4-0.0::INSTR"


def on_state_change(state):
    logger.debug("state changed to {0}".format(state))


class Test(unittest.TestCase):
    def setUp(self):

        import pyspectro.apps

        self.core = PySpectroCore(pyspectro.apps.get_application(32768, 1))

        self.core.on_state_change = on_state_change

        self.core.connect(resourceName)

        logger.debug("Waiting for connection")
        if not self.core.connect_event.wait(10.0):
            logger.debug("Connect failed")
        logger.debug("Connection completed")

    def tearDown(self):

        logger.debug("Disconnecting")
        self.core.disconnect()
        self.core.disconnect_event.wait()

        self.core.terminate()
        self.core = None

    def testSingle(self):
        logger.debug("-----------------")
        logger.debug("testSingle")
        logger.debug("-----------------")

        dev = self.core.device

        with dev.lock:
            dev.numAverages = 1024
            dev.continuousMode = False

        #: First acquisition will take longer for calibration
        self.core.start()
        logger.debug("Waiting for stop event")
        self.core.stop_event.wait()
        self.core.stop_event.clear()

    def testMultiple(self):
        logger.debug("-----------------")
        logger.debug("testMultiple")
        logger.debug("-----------------")

        numAverages = 256

        dev = self.core.device

        with dev.lock:
            Nfft = dev.Nfft
            dev.numAverages = numAverages
            dev.continuousMode = False

        #: First acquisition will take longer for calibration
        self.core.start()
        logger.debug("Waiting for stop event")
        self.core.stop_event.wait()
        self.core.stop_event.clear()

        for _ in range(10):
            self.core.start()
            logger.debug("Waiting for stop event")
            self.core.stop_event.wait()
            self.core.stop_event.clear()

    def testContinuous(self):
        logger.debug("-----------------")
        logger.debug("testContinuous")
        logger.debug("-----------------")

        numAverages = 8192

        dev = self.core.device

        with dev.lock:
            Nfft = dev.Nfft
            dev.numAverages = numAverages
            dev.continuousMode = True
            dev.calibrate()

        period = Nfft * 1 / 2.0e9 * numAverages
        nWordsPerMeasurement = Nfft / 2
        bytesPerWord = 4
        bytesPerSecond = nWordsPerMeasurement / period * bytesPerWord
        logger.info("Required throughput: %s bytes/sec" % bytesPerSecond)

        tstart = time.time()

        logger.info("Starting continuous acquisition")
        self.core.start()
        time.sleep(20)
        logger.info("Stopping")
        self.core.stop()
        logger.info("Waiting for stop event")
        self.core.stop_event.wait()
        self.core.stop_event.clear()

        tstop = time.time()
        elapsed = tstop - tstart
        logger.info("Elapsed time: %s" % elapsed)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
