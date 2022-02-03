# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# -----------------------------------------------------------------------------
import time

from pyspectro.apps import UHSFFTS_32k, UHSFFTS_4k_complex
from pyspectro.applib.processing import convert_raw_to_fs, convert_fs_to_dbfs

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")



resourceName = 'PXI4::4-0.0::INSTR'


def print_status():
    print('  Memory error status: {}'.format(ffts.memoryError))
    print('  Overflow status: {}'.format(ffts.overflow))
    print('  FPGA Core Active: {}'.format(ffts._fpgaCoreIsActive()))
    print('  FPGA Access Memory: {}'.format(ffts._fpgaCanAccessMemory()))
    print('  Measurement count: {}'.format(ffts.measurementCount))
    print('  debug_accum_state: {}'.format(ffts.debug_accum_state()))
    print('  debug_mem_state: {}'.format(ffts.debug_mem_state()))

#ffts = UHSFFTS_32k(resourceName)
ffts = UHSFFTS_4k_complex(resourceName)

ffts.connect()

print('  license_ok: {}'.format(ffts.license_ok))

ffts.instrument.Calibration.SelfCalibrate()

Fs = float(ffts.instrument.sampleRate)
print('Fs = {}'.format(Fs))


Nfft = ffts.Nfft
print('Nfft = {}'.format(Nfft))

ffts.disablePolyphase = False  #: Disable polyphase filter
ffts.numAverages = 1024
ffts.continuousMode = True   #: One-shot measurement
ffts._testMode = True         #: Enable internal CW Generator
ffts._testFreq = 20e6


acqPeriod = Nfft / Fs * ffts.numAverages
print('acqPeriod = {}'.format(acqPeriod))


print_status()

print('Starting Processing')
ffts.startProcessing()

print_status()


time.sleep(5)


ffts.stopProcessing()
ffts.stopProcessing()
ffts.stopProcessing()
print('Stopped Processing')

time.sleep(1)
print_status()



ffts.disconnect()
