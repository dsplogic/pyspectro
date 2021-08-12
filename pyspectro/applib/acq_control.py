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

    
from atom.api import Atom, Typed, Value, Callable, Float, Int, Str
import threading
import queue
import time

import logging
logger = logging.getLogger(__name__)


from ..drivers.Spectrometer import Spectrometer, MemoryConverter

import sys
if sys.version_info[0] == 3:
    EventClass = threading.Event
else:
    EventClass = threading._Event
    

class AcquisitionStats(Atom):
    """ Acquistion statistics
    
    A container for holding statistics of the current acquisition.
    """
    Nmsr_ok      = Value(default=0)            
    Nmsr_drop    = Value(default=0)          
    Nmsr_total   = Value(default=0)  
    Nmsr_blocked = Value(default=0)
    overflow     = Value(default=0)
    memoryError  = Value(default=0)

class AcquisitionDataBuffer(Atom):
    """ Acquisiton result storage
    
    A container to store the results of an acquisiton.
    No type validation is done for speed.
    
    Properties
    ----------
    
    lock : threading.Lock
        This lock must be obtained before reading or writing any other fields.
        
    numAverages: int
        
    """
    
    lock         = Value(factory=threading.Lock)
    numAverages  = Value()
    fftdata      = Value()
    stats        = Typed(AcquisitionStats)

    #: TODO: Consider removing these values form buffer if not needed.
    Nfft         = Value()
    complexData  = Value()


    def clear(self):
        #self.data_ddra   = None
        #self.data_ddrb   = None
        self.fftdata     = None
        self.numAverages = None
        self.stats       = None
        
class AcquisitionControlInterface(Atom):
    """ Acquisition control interface
    
    This class provides a threaded acquisition control manager.  Start, stop,
    polling, and data transfer is done in a worker thread so that the calling
    thread is not blocked.
    """
    
    #: Outgoing event issued when acquisition is started
    start_event = Typed(EventClass, ())

    #: Outgoing event issued when acquisition is stopped
    stop_event = Typed(EventClass, ())
    
    #: Acquisition buffer
    #: Note that passing empty args causes buffer to be created upon initialization
    buffer = Typed(AcquisitionDataBuffer, args=() )

    #: Observable Acquisition State
    acqState = property(lambda self: self._acqState)
    
    #: Outgoing event indicating that data is available in the buffer.
    dataReady  = Typed(EventClass, ())

    #: Incoming event indicating that the buffer is free to be re-used.
    buffer_release  = Typed(EventClass, ())
    
    #: Private storate
    _device      = Typed(Spectrometer)
    _notify      = Callable()
    _numAverages = Int()
    _converter   = Typed(MemoryConverter)
    _acqState    = Str()

    #: Local storage for acquisition statistics
    _stats = Typed(AcquisitionStats)

    #: Polling Interval (seconds)
    _interval  = Float()
    
    #: Command queue for sending commands to the worker thread.
    _command  = Value(factory = queue.Queue)

    #: Private storage for thread object    
    _thread  = Typed(threading.Thread)

    
    def __init__(self, driver):
        """ Initialize an AcquisitionControlInterface
        
        Parameters
        ----------
        driver : SpectrometerApplication
            The driver object must be initialized and connected before creating this
            worker thread object.  
            
        notify : Callable
            A Callable to be run from the worker thread when data is available.  
            The callable should accept one argument that is a AcquisitionDataBuffer
            object containing the data and acquisition status information.  The 
            callable is responsible for safely passing the results to a parent thread
            if necessary.  
            
            
        """
        
        #super(self, AcquisitionControlInterface).__init__()
        
        self._device = driver

        #: Initialize memory converter
        self._converter = MemoryConverter(driver.app.Nfft, driver.app.complexData)
        
        self.buffer.Nfft = driver.app.Nfft
        self.buffer.complexData = driver.app.complexData
    
        #: Set buffer to initially available state
        self.buffer_release.set()
    
    def initialize(self):
        """ Create and start worker thread
        
        """
        logger.debug('Initializing %s' % (self.__class__.__name__))
        self._thread  = threading.Thread(name='Acq',  target=self.acqControlWorker, args=())
        self._thread.start()
        
    def terminate(self):
        """ Terminate worker thread and wait for it to terminate
        
        This method should be called prior to disconnecting the instrument.
        """
        if self._thread:
            logger.debug('Terminating %s' % (self.__class__.__name__))
            self.send_command('_terminate')
            self._thread.join()
        
    def send_command(self, cmd):
        """ Send command to worker thread
        
        Valid Commands:
        
        start:
            Start acquisition.  A startProcessing command will be issued through the driver.
            Continuous mode should be set on/off prior to issuing this command.
        
        stop:
            Stop acquisition.
        
        """
        if cmd in ['start', 'stop', '_terminate']:
            self._command.put(cmd)
        else:
            raise Exception('Command %s invalid' % cmd)

    def _get_cmd(self):
        """ Check for new command.
        
        Get command from queue.  Return empty string if queue is empty.
        """
        try:
            cmd = self._command.get(False)
        except:
            cmd = ''
            
        if cmd not in ['', 'start', 'stop','_terminate']:
        
            msg = 'Invalid command received: %s' % cmd
            logger.error(msg)
            raise Exception(msg)
        
        return cmd

    def update_buffer(self):
        """ Update acquisiton buffer with SpectroCore data
        
        """
        
        got_buffer_lock = self.buffer.lock.acquire(False) #: Non-blocking

        if got_buffer_lock:  
            
            #logger.debug('Got buffer lock')
            try:
                with self._device.lock:
                    data_ddra    = self._device.read_memory(1)
                    data_ddrb    = self._device.read_memory(2)
                    
            finally:
                self.buffer.lock.release()
                #logger.debug('Released buffer lock')
                
            self.buffer.fftdata      = self._converter.process(data_ddra, data_ddrb)
            self.buffer.numAverages  = self._numAverages
            self.buffer.stats        = self._stats
            
            self.dataReady.set()
            
            logger.info('Measurement {0} complete'.format(self._stats.Nmsr_total))
                
        else:
            logger.warning('Buffer blocked, results not read from instrument')
            #: Buffer not available
            self._stats.Nmsr_blocked += 1

                
    def acqControlWorker(self):
        """ Acquisition control worker task
        
        This task implements a state machine with the following states:
        
            idle : 
                Ready to recive a start acquisition command
                
            acquiring:
                Acquisition (continuous or one-shot) in process.
            
            dataReady:
                Measurement being transferred from instrument.  
                At the end of transfer, the notify callback will be issued
            
            terminating:
                Worker thread is in the process of terminating.  At the end of 
                this state, the worker thread will terminate
        """
        
        ACQ_STATE = 'idle'

        prior_count  = 0
        
        #: Main thread loop
        while ACQ_STATE != 'terminated':

            time.sleep(self._interval)

            #: Report current acquisition state
            #: Setting string value should be atomic/thread safe
            self._acqState = ACQ_STATE
            #print('Current State: %s' % ACQ_STATE)

            #:
            #: Acquisition State Machine
            #:            
            if ACQ_STATE == 'idle':
                
                #: Process commands
                cmd = self._get_cmd()
                
                if cmd == 'start':
                    prior_count  = 0
                    self._stats = AcquisitionStats()
                    ACQ_STATE   = 'acquiring'
                    
                    with self._device.lock:
                        self._numAverages = self._device.numAverages #: Store to log with result
                    
                    acqPeriod = self._device.Nfft * 1/2e9 * self._numAverages

                    logger.debug('Acquisition period: %s msec' % (acqPeriod * 1000.0))
                    
                    pollsPerPeriod = 10.0

                    self._interval = acqPeriod/pollsPerPeriod
                    
                    logger.debug('Setting polling period to: %s msec' % (self._interval * 1000.0))
                    
                    with self._device.lock:
                        self._device.startProcessing()
                    
                    self.start_event.set()
                
                elif cmd == 'stop':
                    pass  #: Ignore command

                elif cmd == '_terminate':
                    ACQ_STATE = 'terminating'
                    
            elif ACQ_STATE == 'acquiring':

                #: Process commands
                cmd = self._get_cmd()
                
                if cmd == 'stop':
                    with self._device.lock:
                        self._device.stopProcessing()
                    self.stop_event.set()
                    ACQ_STATE = 'idle'
                    
                
                elif cmd == '_terminate':
                    with self._device.lock:
                        self._device.stopProcessing()
                    self.stop_event.set()
                    ACQ_STATE = 'terminating'
                    
                else:
                    #: if cmd = '' or 'start'
                    with self._device.lock:
                        
                        #: Current count read from Spectrometer hardware
                        currentCount = self._device.measurementCount
                    
                    #:print('Current measurement count: %s.  Waiting for %s' % (currentCount, prior_count+1))
                    
                    if currentCount == prior_count:
                        ACQ_STATE = 'acquiring'

                    if currentCount == prior_count + 1:
                        ACQ_STATE = 'transferring'
                        self._stats.Nmsr_ok += 1
                        prior_count = currentCount
                        
                    elif currentCount > prior_count + 1:
                        ACQ_STATE = 'transferring'
                        self._stats.Nmsr_ok += 1
                        self._stats.Nmsr_drop += currentCount - prior_count - 1
                        prior_count = currentCount

                    self._stats.Nmsr_total = currentCount
                    
            elif ACQ_STATE == 'transferring':

                self.update_buffer()

                #: Update state based on current mode                
                if self._device.continuousMode:
                    ACQ_STATE = 'acquiring'
                else:
                    with self._device.lock:
                        self._device.stopProcessing()
                    self.stop_event.set()
                    ACQ_STATE = 'idle'
                    
                
            elif ACQ_STATE == 'terminating':
                
                ACQ_STATE = 'terminated'
            
            else:
                raise Exception('Invalid acquisition state detected')  
                                  

if __name__ == '__main__':

    pass
