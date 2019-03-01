#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------

from atom.api import Atom, Value, Bool, Property, Int, Tuple, Enum, Float

import matplotlib.pyplot as plt
import numpy as np

import logging
logger = logging.getLogger(__name__)

import time

def onclick(event):
    logger.debug('button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
        event.button, event.x, event.y, event.xdata, event.ydata))
 

class MplFigure(Atom):
    """ An updatable Matplotlib figure
    
    """
    
    #: Data to plot
    xdata = Value()
    ydata = Value()
    
    figure   = Value()
    ax       = Value()

    #: Plots on current axis
    #: type: matplotlib.lines.Line2D (subclass of matplotlib.artist.Artist)
    line     = Value()
    selected = Value()
    
    #: Index of the current selection
    ind_selected = Value()
    val_selected = Tuple(default=(0,0))
    selection_active = Bool()
    
    xlabel   = Property()
    ylabel   = Property()
    
    xrange   = Property()
    yrange   = Property()
    
    autoscale = Bool(True)
    
    disableRefresh = Bool(False)
    
    number = property(lambda self: self.figure.number)
    
    def __init__(self, *args, **kwargs):

        #: Create initial figure items
        fig, ax = plt.subplots()
        self.figure = fig
        self.ax = ax
        self.line,     = ax.plot([],[], picker= 5)
        self.selected, = ax.plot([], [], 'o', ms=5, alpha=0.9,
                                 color='yellow', visible=False)

        super(MplFigure, self).__init__(*args, **kwargs)
        
    def _get_xrange(self):
        
        return self.ax.get_xrange()
    
    def _set_xrange(self, minmax):
        
        self.ax.set_xlim(minmax[0], minmax[1])
        
    def _get_yrange(self):
        return self.ax.get_yrange()
        
    def _set_yrange(self, minmax):
        
        self.ax.set_ylim(minmax[0], minmax[1])
            
    def _set_xlabel(self, val):
        self.ax.set_xlabel(val)

    def _get_xlabel(self):
        return self.ax.get_xlabel()
    
    def _set_ylabel(self, val):
        self.ax.set_ylabel(val)

    def _get_ylabel(self):
        return self.ax.get_ylabel()

    def format_data(self):
        """ Format data prior to rendering
        
        This method can be overridden by subclasses
        
        Returns:
        
        tuple: (xdata, ydata)
        """
        return (self.xdata, self.ydata)

    def redraw(self, flush = False):
        
        if self.disableRefresh:
            
            return

        xdata, ydata = self.format_data()
        
        self.line.set_xdata(xdata)
        self.line.set_ydata(ydata)
        
        if self.ind_selected:
            
            self.selected.set_visible(True)
            
            self.val_selected = (xdata[self.ind_selected], ydata[self.ind_selected])
            
            self.selected.set_data(self.val_selected)
            
        else:

            self.selected.set_visible(False)
        
        if self.autoscale:
             
            #: Note that if you have used set_xlim() on the same axes before, relim() autoscale_view() will NOT work. 
            #: In this case, autoscale() should be used instead (tested on 1.5.x). 
             
            #: Need both of these in order to rescale
            self.ax.relim(visible_only=True)
            self.ax.autoscale_view() # scalex=False, scaley=True
            
                    
        self.figure.canvas.draw()
        
        if flush:
            self.figure.canvas.flush_events()
        
#     def update_data(self):
#         
#         self.line.set_xdata(self.xdata)
#         self.line.set_ydata(self.ydata)
#         
#         
#         self.redraw()
        
    def freeze(self):
        
        plt.ioff()
        time.sleep(1)
        print('plotting')
        plt.plot(figure = self.figure)
        time.sleep(1)
        print('done')
        #self.figure.show()

    def clear(self):
        
        self.figure.clear()
        
    def close_window(self):
        
        plt.close(self.figure)


#from pyspectro.common.helpers import scalePlotData
from pyspectro.applib.processing import convert_raw_to_fs, convert_fs_to_dbfs, convert_fs_to_dBm


class SpectrumFigure(MplFigure):
    
    Nfft          = Int(32768)
    
    complexData   = Bool(False)
    
    sampleRate    = Float(2.0e9)

    numAverages   = Int(1024)
    
    units         = Enum( 'dBm', 'dB-FS', 'FS') #, 'mW'
    
    voltageRange  = Enum(1.0, 2.0)
    
    
    def __init__(self, *args, **kwargs):
        
        super(SpectrumFigure, self).__init__(*args, **kwargs)
        
        self.xlabel = 'Frequency (MHz)'
        
        self.update_ylabel()
        
        self.update_xrange()
        
        self.yrange = (-110, 10)
        
        self.ax.grid(True)

    def update_ylabel(self):
        
        self.ylabel = 'Power (%s)' % self.units
        
    def update_xrange(self):
        """ Set frequency range (in MHz)
        
        """
        
        if self.complexData:
            
            self.xdata = self.sampleRate * (np.arange(self.Nfft) - self.Nfft/2.0)/ float(self.Nfft) / 1.0e6    
            
            self.xrange = (-self.sampleRate/2.0/1.0e6, +self.sampleRate/2.0/1.0e6)
         
            
        else:
            
            self.xdata = self.sampleRate * np.arange(self.Nfft/2.0) / float(self.Nfft) / 1.0e6    
            
            self.xrange = (0, self.sampleRate/2.0/1.0e6)

    
    def format_data(self):
        
        ydata = self.ydata
        
        fft_fs = convert_raw_to_fs(ydata, self.numAverages, self.complexData)
        
        if self.units == 'FS':
            return self.xdata, fft_fs
        
        elif self.units == 'dB-FS': 
            fft_dbfs = convert_fs_to_dbfs(fft_fs, self.complexData)
            return self.xdata, fft_dbfs
        
        elif self.units == 'dBm': 
            fft_dbfs = convert_fs_to_dBm(fft_fs, self.complexData, self.voltageRange)
            return self.xdata, fft_dbfs
        
        else:
            raise Exception('Units not yet supported')

    

if __name__ == "__main__":

    sf = SpectrumFigure(numAverages = 4)
    plt.show()
    
    
