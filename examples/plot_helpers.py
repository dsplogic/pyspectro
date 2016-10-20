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

""" Demonstration helpers for plotting fft results  

"""

from pyspectro.applib.processing import  convert_raw_to_fs, convert_fs_to_dbfs
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter


def plot_waterfall(rawfftdata , numAverages, msrmnt_idx):
    
    Fs = 2.0e9 #: Sample Rate
    
    N,Nfftdiv2 = np.shape(rawfftdata)

    #: Compute frequency axis
    f = np.arange(Nfftdiv2, dtype=np.float )
    df = Fs / 2.0 / Nfftdiv2
    f = f * df
    
    #: Convert units
    fft_fs = convert_raw_to_fs(rawfftdata, numAverages[0])
    fft_dbfs = convert_fs_to_dbfs(fft_fs)

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    X = f / 1.0e6
    Y = np.arange(N)
    X, Y = np.meshgrid(X, Y)
    surf = ax.plot_surface(X, Y, fft_dbfs, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Time")
    plt.show()




def plot_raw_data(rawfftdata, numAverages):
    Fs = 2.0e9 #: Sample Rate
    fft_fs = convert_raw_to_fs(rawfftdata, numAverages)
    fft_dbfs = convert_fs_to_dbfs(fft_fs)
    
    """ This is a utility function used to plot data """    
    #: Compute frequency axis
    Nfft = 2*fft_dbfs.size
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
    plt.plot(f, fft_dbfs)
    plt.show()

    
    