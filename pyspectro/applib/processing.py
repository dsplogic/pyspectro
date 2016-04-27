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


import numpy as np




def convert_raw_to_fs(fft_raw, numAverages):
    """ Convert raw measurement to units of RMS power relative to full-scale input

    This function assumes the input signal is real and 
    fftdata.size = Nfft/2
    """
    
    #: Assume real data for number of frequencies    
    nfftDiv2 = np.double(fft_raw.size)
    
    #:  Compute scale factor
    scale = (nfftDiv2)**2 * np.double(numAverages)

    #: Apply correction from manual calibration
    correction_db = -0.43
    correction = 10.0**(correction_db/20.0)
    

    fft_fs = fft_raw * (2*correction) **2 / scale #: Mult by 2*2 for real input 
    
    return fft_fs

def convert_fs_to_dbfs(fft_fs, vRange = 1.0):

    fft_dbfs = 10.0*np.log10(fft_fs*1.0)
    
    return fft_dbfs

    
def convert_fs_to_dBm(fft_fs, vRange = 1.0):

    gain_dbm_to_dbfs = 6.99
    
    if vRange == 2.0:
        gain_dbm_to_dbfs += 6.02
    
    return convert_fs_to_dbfs(fft_fs, vRange) + gain_dbm_to_dbfs
    
    