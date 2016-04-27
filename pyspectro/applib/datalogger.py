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



import threading
from atom.api import Atom, Str, Value, Enum, Int, Typed, List
from .acq_control import AcquisitionDataBuffer

import numpy as np

import h5py

import logging
from __builtin__ import file
logger = logging.getLogger(__name__)

            
from .processor import CommandThread            
            

def log_acquisition_data(acq_buf):
    """
    
    """
    with acq_buf.lock:
        
        logger.info('Logging acq_buf')
        


class SpectrumDataLogger(CommandThread):
    
    store_done = Typed(threading._Event, ())

    _acq_buf = Typed(AcquisitionDataBuffer)
    
    _valid_commands = ['start', 'stop', 'store','terminate']

    _state   = Enum('idle', 'prepare', 'ready', 'running', 'storing') 
    
    _file = Value()
    
    _groupid = Int(0)
    
    _group = Value()
    
    _dset_fftdata      = Value()
    _dset_num_averages = Value()
    _dset_msrmt_num    = Value()
    
    _max_records_per_dataset = Int(100)
    
    _current_idx = Int(0)
    
    def __init__(self, acq_buf):
        self._acq_buf = acq_buf
    
    def terminate(self):
        """ A reimplemented terminate method
        
        """
        self.send_command('terminate')
        super(SpectrumDataLogger, self).terminate()
        
                 
    def _main_loop(self):
        """ Connection state machine controller
        
        """

        self._file = h5py.File("pyspectro_data_log.hdf5", "w")


        while True: # not self._terminate.wait(0.1):
            
            if self._state   == 'idle':
                self._state = 'prepare'
                
            elif self._state == 'prepare':

                N = self._max_records_per_dataset
                
                #: Create a group to contain the next acquisition
                self._groupid += 1
                
                groupname = 'acq{0:08d}'.format(self._groupid)
                
                self._group =  self._file.create_group(groupname)
                
                self._dset_fftdata       = self._group.create_dataset("fftdata",      (N,16384), dtype='float64')
                self._dset_num_averages  = self._group.create_dataset("num_averages", (N,),      dtype='int32')
                self._dset_msrmt_num     = self._group.create_dataset("msrmt_num",    (N,),      dtype='int32')
                #self._dset_voltageRange  = self._group.create_dataset("msrmt_num",    (N,),      dtype='int32')
                
                self._state = 'ready'   
                logger.debug('Prepared new group %s' % self._groupid)
                
            elif self._state == 'ready':

                #: Wait for command
                cmd = self._command.get()
                
                #cmd = self._get_cmd()
                if cmd == 'start':
                    
                    self._state = 'running'
                    
                elif cmd == 'terminate':
                    break
            
            elif self._state == 'running':
                
                cmd = self._get_cmd()
                if cmd == 'store':
                    self._state = 'storing'
                elif cmd == 'stop':
                    self._state = 'prepare'
            
            elif self._state == 'storing':
                
                if self._current_idx < self._max_records_per_dataset:
                    
                    with self._acq_buf.lock:
                        
                        logger.debug('Storing data idx %s' % self._current_idx)
                        
                        #: TODO: Some stats only need to be stored once per group.
                        self._dset_fftdata[self._current_idx, :]   =  self._acq_buf.fftdata
                        self._dset_num_averages[self._current_idx] =  self._acq_buf.numAverages  
                        self._dset_msrmt_num[self._current_idx]    =  self._acq_buf.stats.Nmsr_total
                        #self._dset_voltageRange[self._current_idx] =  self._acq_buf.voltageRange

                        # Increment idx for next measurement
                        self._current_idx += 1
                        # Store measurement count
                        self._group.attrs['count'] = self._current_idx
                
                else:
                    logger.debug('Logger full, ignoring store command')
                    
                #: Produce store_done event (even if logging ended)         
                self.store_done.set()
                    
                self._state = 'running'
        
        #: Exiting main loop
        self._file.attrs['n_acq'] = self._groupid - 1
                    
        self._file.flush()
        self._file.close()
            
        self._terminate.clear()

                 
class SpectrumDataReader(Atom):
    """ Spectrum log file reader 
    
    Read a spectrom log file in HDF5 File format
    """
    
    #: Number of acquisitions
    acquisitions  = property(lambda self: self._acquisitions)

    _filepath = Str()
    _file     = Value() 
    _acquisitions = List()
    
    def __init__(self, file):
        """ Initialize the reader
        
        Parameters
        ----------
        file: str
            Path of file to read
            
        """
        self._filepath = file
        self._file = h5py.File(file,'r')
        n_acq = self._file.attrs['n_acq']
        
        logger.debug('Opened file {0}'.format(self._filepath))
        logger.debug('Found {0} acquisitions'.format(n_acq))
        
        #: Sort by acquisiton name (integer order)
        keys = sorted(self._file.keys())
        
        #: Note that the HDF5 file always one extra empty group, corresponding to the
        #: group that was prepared for the following measurement.  We strip it out here
        
        acquisitions = []
        for key in keys[0:n_acq]:
            acquisitions.append(self._file[key])
            
        self._acquisitions = acquisitions 
        
        
            
            
        


#     def iter_acquisitions(self):
#         """ Iterate over each acquisiton 
#          
#         """
#         
#         return len(self._file.keys())
    
    
        
        
#     def info(self):
#         result = {}
#         result['Nacq'] = self.num_acquisitions()
#         
#         return result
        
        
        
        
if __name__ == '__main__':

    pass
