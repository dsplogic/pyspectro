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


import numpy as np



def convert_raw_to_fs(fft_raw, numAverages, complexData):
    """ Convert raw measurement to units of digital mean-square power relative to full-scale input

    The following equation represents a full-scale complex CW input, where A = 1.0.
      A*( cos(2*pi*Fc*t) + i*sin(2*pi*Fc*t) )
    and the ADC digital input range is [-1, 1), i.e. (12-bit wide with 11 bit scale).

    For real FFT (with no interleaving), the imaginary (second channel) input is zero.

        Input Type:              Real                     Complex
        --------------------     -------------------      ---------------------------------------
        Full-scale CW (A=1)      A*( cos(2*pi*Fc*t)       A*( cos(2*pi*Fc*t) + i*sin(2*pi*Fc*t) )
        Power (rms)              A/sqrt(2)                A
        Power (ms)               A^2 / 2                  A^2
        Peak |FFT| output        A*Nfft/2                 A*Nfft
        Peak |FFT|^2 output      (A*Nfft/2)^2             (A*Nfft)^2

    fft_raw :
        Acquisiton buffer data.
        Length Nfft for complex input and Nfft/2 for real input

    """

    if complexData:

        #: Assume real data for number of frequencies
        if fft_raw.ndim == 1:

            N = 1;
            Nfft = np.double( np.size(fft_raw) )
            nfftDiv2 = Nfft/2.0

        elif fft_raw.ndim == 2:

            N, Nfft = np.shape(fft_raw)
            Nfft = np.double(Nfft)
            nfftDiv2 = Nfft/ 2.0

        #:  Compute maximum output level for normalization
        scale = np.square(Nfft) * np.double(numAverages)

    else:

        #: Assume real data for number of frequencies
        if fft_raw.ndim == 1:

            N = 1;
            nfftDiv2 = np.double(np.size(fft_raw))
            Nfft = 2.0* nfftDiv2

        elif fft_raw.ndim == 2:

            N,nfftDiv2 = np.shape(fft_raw)
            nfftDiv2 = np.double(nfftDiv2)
            Nfft = 2.0* nfftDiv2

        #:  Compute scale factor
        scale = np.square(Nfft) * np.double(numAverages) / 2.0

    #: Mean square power:
    fft_fs = fft_raw / scale


#     #: Apply correction from manual calibration
#     correction_db = 0.0
#     #correction_db = -0.43
#     correction = 10.0**(correction_db/20.0)



    return fft_fs

def convert_fs_to_dbfs(fft_fs, complexData = True):

    if complexData:

        fft_dbfs = 10.0*np.log10(fft_fs)

    else:

        #: For real data, need to compensate for diff in full scale
        fft_dbfs = 10.0*np.log10(fft_fs*2)

    return fft_dbfs


def convert_fs_to_dBm(fft_fs, complexData = True, vRange = 1.0):

    gain_dbm_to_dbfs = 6.99

    if vRange == 2.0:
        gain_dbm_to_dbfs += 6.02

    return convert_fs_to_dbfs(fft_fs, complexData) + gain_dbm_to_dbfs
