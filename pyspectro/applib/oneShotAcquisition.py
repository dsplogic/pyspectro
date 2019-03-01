#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
#------------------------------------------------------------------------------
from __future__ import (division, print_function, absolute_import)

"""
Created on Feb 22, 2016

@author: M. Babst
"""


import numpy as np
import matplotlib.pyplot as plt

from pyspectro.common.helpers import Timer
from pyspectro.applib.processing  import convert_raw_to_fs, convert_fs_to_dbfs
from pyspectro.applib.acq_control import AcquisitionControlInterface


import logging
logging.basicConfig(level=logging.DEBUG)


logger = logging.getLogger(__name__)


resourceName = 'PXI4::4-0.0::INSTR'



def plotresult(dBspectrum, Fs):
    #: Compute frequency axis
    f = np.arange(16384.0, dtype=np.float )
    df = Fs / 2.0 / 16384.0
    f = f * df

    #: Plot data
    fig = plt.figure()

    plt.xlabel("Frequency")
    plt.ylabel("Power")
    plt.grid(True)
    axes = plt.gca()
    axes.set_ylim([-120, 0])
    plt.plot(f, dBspectrum)
    plt.show()


def process_buffer(acqbuffer, complexData = False):
    logger.debug('Processing buffer')

    with acqbuffer.lock:
        logger.debug('Acquired buffer lock')

        if acqbuffer.fftdata is not None:

            fft_fs = convert_raw_to_fs(acqbuffer.fftdata, acqbuffer.numAverages)

            fft_dbfs = convert_fs_to_dbfs(fft_fs, complexData)

            plotresult(fft_dbfs, Fs)

        else:
            logger.warning('Buffer empty')

    logger.debug('Released buffer lock')


if __name__ == '__main__':

    from pyspectro.apps import UHSFFTS_32k, UHSFFTS_4k_complex

    #: Connect to instrument
    #ffts = UHSFFTS_32k(resourceName)
    ffts = UHSFFTS_4k_complex(resourceName)

    try:
        ffts.connect()

        Fs = ffts.instrument.sampleRate

        ffts.numAverages = 1024

        #: Start acquisiton controller thread
        acqControl = AcquisitionControlInterface(ffts) #:, notify = dataReadyCallback )
        try:
            acqControl.initialize()

            acqControl.send_command('start')

            acqControl.dataReady.wait()
            acqControl.dataReady.clear()

            process_buffer(acqControl.buffer)

        finally:
            acqControl.terminate()

    finally:
        ffts.disconnect()
