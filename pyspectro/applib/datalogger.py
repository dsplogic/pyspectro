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



import threading
import h5py
import logging
import os
import numpy as np
from atom.api import Atom, Str, Value, Enum, Int, Typed, List, Bool
from .acq_control import AcquisitionDataBuffer
from .processor import CommandThread
#from __builtin__ import file
import time

logger = logging.getLogger(__name__)

#: Get user home directory
HOME = os.path.expanduser('~')
PYHOME =  os.path.join(HOME, 'pyspectro')
if not os.path.exists(PYHOME):
    os.makedirs(PYHOME)

import sys
if sys.version_info[0] == 3:
    EventClass = threading.Event
else:
    EventClass = threading._Event

class SpectrumDataLogger(CommandThread):
    """ Spectrum Data Logger

    This thread logs instrument data.

    A new file is created for each acquisition.

    Properties:
    -----------

    max_measurements_per_acq : int

        The maximum number of measurements recorded per acquisition
        in continuous mode. Measurements beyond this number
        will not be recorded

    """

    Nfft = Int()
    complexData = Bool()

    #: Maximum number of measurements per dataset
    max_measurements_per_acq = Int(100)

    #: An event that can be used when storing to data files is complete
    store_done = Typed(EventClass, ())


    _acq_buf = Typed(AcquisitionDataBuffer)

    _valid_commands = ['start', 'stop', 'store','terminate']

    _state   = Enum('idle', 'prepare', 'ready', 'running', 'storing')

    _file = Value()

    _groupid = Int(0)

    _group = Value()

    _dset_fftdata      = Value()
    _dset_num_averages = Value()
    _dset_msrmt_num    = Value()
    _current_idx = Int(0)

    def __init__(self, Nfft, complexData, acq_buf):
        """ Initialize the SpectrumDataLogger thread

        Parameters
        ----------
        acq_buf : AcquisitionDataBuffer
            Acquisiton Data Buffer
        """
        self._acq_buf = acq_buf

    def terminate(self):
        """ A reimplemented terminate method

        """
        self.send_command('terminate')
        super(SpectrumDataLogger, self).terminate()


    def _main_loop(self):
        """ Connection state machine controller

        """


        #: Main Loop
        while True:

            if self._state   == 'idle':
                self._state = 'prepare'

            elif self._state == 'prepare':

                #: Prepare for a new acquisition
                #: Create file to hold acquisiton data
                timestr = time.strftime("%Y%m%d_%H%M%S")
                fname = "%s-pyspectro_acq_data.hdf5" %  timestr
                fullfile = os.path.join(PYHOME, fname)
                self._file = h5py.File(fullfile, "w")


                N = self.max_measurements_per_acq

                #: Create a group for each acquisition
                self._groupid += 1

                groupname = 'acq{0:08d}'.format(self._groupid)

                self._group =  self._file.create_group(groupname)

                if self.complexData:
                    self._dset_fftdata       = self._group.create_dataset("fftdata",      (N, self.Nfft), dtype='float64')
                else:
                    self._dset_fftdata       = self._group.create_dataset("fftdata",      (N, self.Nfft//2), dtype='float64')

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

                    #: Acquisiton is complete.  Close and flush file.  Get ready for another.
                    self._file.flush()
                    self._file.close()

                    self._state = 'prepare'

            elif self._state == 'storing':

                if self._current_idx < self.max_measurements_per_acq:

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
                        #: Set acquisition count (will always be one in this case)
                        self._file.attrs['n_acq'] = self._groupid

                else:
                    logger.debug('Logger full, ignoring store command')

                #: Produce store_done event (even if logging ended)
                self.store_done.set()

                self._state = 'running'

        #: Exiting main loop
        #: Close and delete file that was prepared but not used
        self._file.flush()
        self._file.close()
        os.remove(fullfile)

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

        #: Sort by acquisiton name (integer order), e.g. acq00000001
        keys = sorted(self._file.keys())

        acquisitions = []
        for key in keys[0:n_acq]:
            acqgroup = self._file[key]

            fftdata = acqgroup['fftdata']
            nrec,fftdiv2 = np.shape(fftdata)
            count = acqgroup.attrs['count'] #: Measurement count

            acq_result = {}
            acq_result['name']          = key
            acq_result['msrmnt_count']  = count
            acq_result['fftdata']       = fftdata[range(count), :] #: Trim to size
            acq_result['num_averages']  = acqgroup['num_averages']
            acq_result['msrmnt_idx']    = acqgroup['msrmt_num']

            acquisitions.append(acq_result)

        self._acquisitions = acquisitions





if __name__ == '__main__':

    pass
