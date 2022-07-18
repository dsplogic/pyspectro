""" 4k complex data collection example

This example demonstrates continuous acquisition and data processing
using the threaded acquisition controller

A internal test signal is generated at 100 MHz.
For each measurement, the peak value and frequency are retrieved.

"""
import logging

import numpy as np

from pyspectro.applib.acq_control import AcquisitionControlInterface
from pyspectro.apps import UHSFFTS_4k_complex
from pyspectro.common.atom_helpers import prettyMembers

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")

resourceName = "PXI4::4-0.0::INSTR"

# Create the spectrometer object, connect and calibrate
ffts = UHSFFTS_4k_complex(resourceName)
ffts.connect()
ffts.instrument.Calibration.SelfCalibrate()

# Set measurement period and print some info
# Note that when measurement period is reduced, some measurements may be blocked or missed,
# depending upon system performance
ffts.numAverages = 8192
period = ffts.Nfft * 1 / ffts.sampleRate * ffts.numAverages
logger.info('Measurement period: {}'.format(period))
if ffts.app.complexData:
    nWordsPerMeasurement = ffts.Nfft
else:
    nWordsPerMeasurement = ffts.Nfft / 2
bytesPerWord = 4
bytesPerSecond = nWordsPerMeasurement / period * bytesPerWord
logger.info("Required throughput: %s bytes/sec" % bytesPerSecond)

# Compute frequency bins for later use
Fs = ffts.sampleRate
print("Fs={}".format(Fs))
freq_init = -Fs / 2
freq_step = Fs / ffts.Nfft

# Enable internal digital CW Tone generator
# This will bypass external signal input
ffts._testMode = True
ffts._testFreq = 100e6

"""Test continuous acquisition with minimal data processing"""
# Create an acquisition controller object and initialize it
acqControl = AcquisitionControlInterface(ffts)
acqControl.initialize()

# Set spectrometer to continuous mode
ffts.continuousMode = True

# Start acquisition
acqControl.send_command("start")

#: Process 10 sequential measurements
Nmeasurements = 20

for k in range(Nmeasurements):

    # Wait for data to be ready
    acqControl.dataReady.wait()

    # Acquire buffer lock
    with acqControl.buffer.lock:

        if acqControl.buffer.fftdata is not None:

            # Read data from buffer
            fftdata = acqControl.buffer.fftdata

            # Perform some basic processing (get max value)
            max_value = np.amax(fftdata)
            max_idx = np.argmax(fftdata)
            max_freq = freq_init + freq_step * max_idx
            logger.info("Max value: {} @ freq {} MHz".format(max_value, max_freq / 1.0e6))

        else:
            logger.warning("Buffer empty")

    # Clear data ready flag
    acqControl.dataReady.clear()

# Stop acquisition
acqControl.send_command("stop")

logger.info(prettyMembers(acqControl.buffer.stats))

acqControl.terminate()
logger.info('Acquisition controller terminated')

