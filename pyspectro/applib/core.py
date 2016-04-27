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


from atom.api import Atom, Typed, Str, Enum, Bool, Callable, observe, Value

from .acq_control import AcquisitionControlInterface, AcquisitionDataBuffer

from ..drivers.Spectrometer import Spectrometer, UHSFFTS_32k
from .connection import ConnectionManager
from .datalogger import SpectrumDataLogger

import threading
from .processor import CommandThread, TimedProcessor, ProcessTask
from .instrument_props import get_instrument_properties_string

import logging
logger = logging.getLogger(__name__)


class PyspectroApp(Atom):
    pass


class PySpectroCore(CommandThread):
    """ Application Core
     
    """
    on_state_change    = Callable()
    on_user_data_ready = Callable()
    on_heartbeat_task  = Typed(ProcessTask)
    
    #: Outgoing thread events
    connect_event         = Typed(threading._Event, ())
    disconnect_event      = Typed(threading._Event, ())
    start_event           = Typed(threading._Event, ())
    stop_event            = Typed(threading._Event, ())
    
    
    #: Incoming event to indicate user has requested data
    user_data_request     = Typed(threading._Event, ())
    #: Outgoing indicate indicating that the user_data buffer has been loaded
    user_data_ready_event = Typed(threading._Event, ())
    #: User data buffer.  Should be read using lock
    user_data = Typed(AcquisitionDataBuffer, args=())

    #: Device driver 
    #: Can be accessed by main thread when done with care
    #: Set properties only core is in idle state. 
    #: Use lock whenever setting properties
    #: Read minimal properties during acquisition 
    device = Typed(Spectrometer)

    #: Valid commands that can be sent to core thread
    _valid_commands = ['connect','disconnect','start','stop','terminate']
    

    #: Child threads        
    _acq  = Typed(AcquisitionControlInterface)
    _con  = Typed(ConnectionManager)
    _log  = Typed(SpectrumDataLogger)
    _hb   = Typed(TimedProcessor)

    #: Heartbeat event produved by hearbeat thread
    _heartbeat_event = Typed(threading._Event, ())
    
    _logging = False
 
    #: Private storage for worker thread
    _state        = Enum('disconnected','connecting','idle','acq_start','acquiring','acq_done')
    
    _initialized  = Bool()
    
    def __init__(self, *args, **kwargs):

        super(PySpectroCore, self).__init__(*args, **kwargs)
        
        self.device = UHSFFTS_32k()
        
        self._con = ConnectionManager(self.device)
        self._acq = AcquisitionControlInterface(self.device)
        self._log = SpectrumDataLogger(self._acq.buffer)

        self._hb = TimedProcessor(interval = 1.0, 
                                  task = self._heartbeat_event.set, 
                                  args = (), 
                                  kwargs = {})
        
        self.initialize()
        
        logger.debug('Initialized {0}'.format(self.__class__.__name__))
        logger.info('Initialization complete')
        
    
    @observe('_state')
    def _state_change_handler(self, change):
        if self.on_state_change:
            self.on_state_change(change['value'])
            
            
    def initialize(self):
        """ A re-implemented initializer
        """
        if not self._initialized:
            #: Intialize child thread
            self._con.initialize(thread_name = 'ConnMgr')
            self._acq.initialize()
            self._log.initialize(thread_name = 'Logger')
            self._hb.start(thread_name = 'heartbeat')
            
            #: Initialize self thread
            super(PySpectroCore, self).initialize(thread_name = 'Core')
            
            self._initialized = True

    def terminate(self):
        if self._initialized:
            
            self.send_command('terminate')
            
            #: Terminate own thread
            #: clean shutdown is performed within thread
            super(PySpectroCore, self).terminate()

            #: terminate other threads
            self._con.terminate()
            self._acq.terminate()
            self._log.terminate()
            self._hb.stop()
            self._initialized = False


    def connect(self, resourceName):
        
        with self.device.lock:
            self.device.resourceName = resourceName
            
        self.send_command('connect')
        
    def disconnect(self, blocking = False):
        
        self._hb.stop()

        self.send_command('disconnect')
        
        

    def start(self):
        self.send_command('start')
        
    def stop(self):
        self.send_command('stop')

    def _main_loop(self):
        """ State machine controller
         
        """
        #: Initialize comtypes for this thread using flags defined in sys.coinit_flags        
        import comtypes
        comtypes.CoInitializeEx()
 
        while True: #not self._terminate.wait(0.1):
             
            if self._state   == 'disconnected':

                cmd = self._get_cmd()
                if cmd:
                    if cmd == 'connect':
                        self._con.connect()
                        self._state = 'connecting'
                    elif cmd == 'terminate':
                        break
                    else:
                        logger.warning('{0} ignored command {1} in state {2}'.format(self.__class__.__name__, cmd, self._state))
                    

            elif self._state == 'connecting':
            
                if self._con.connected.is_set():
                    self._con.connected.clear()
                    self._state = 'idle'
                    self.connect_event.set()

                    #: Readback status for log
                    with self.device.lock:
                        result = get_instrument_properties_string(self.device)
                    logger.info(result)

                     
            elif self._state == 'idle':
                
                cmd = self._get_cmd()
                if cmd:
                    if cmd == 'disconnect':
                        self._con.disconnect()
                        self._con.disconnected.wait()
                        self._state = 'disconnected'
                        self.disconnect_event.set()
                        
                    elif cmd == 'start':
                        self._state = 'acq_start'
                        self._acq.send_command('start')
                        self._log.send_command('start')
                        
                    elif cmd == 'terminate':
                        break
                    
                    else:
                        logger.warning('{0} ignored command {1} in state {2}'.format(self.__class__.__name__, cmd, self._state))
                    
                if self._heartbeat_event.is_set():
                    self._heartbeat_event.clear()
                    if self.on_heartbeat_task:
                        self.on_heartbeat_task._execute()
                
                
            elif self._state == 'acq_start':
                #: wait for acquisition to start
                if self._acq.start_event.is_set():
                    self._acq.start_event.clear()
                    self._state = 'acquiring'
                    logger.debug('Acquisition start event')
                    self.start_event.set()
                 
            elif self._state == 'acquiring':
                
                #: Handle data ready events
                #: Perform minimal processing here.
                
                if self._acq.dataReady.wait(0.5): #self._acq.dataReady.is_set():
                    self._acq.dataReady.clear()

                    #: Process buffer data
                    self._log.send_command('store')
                    #: wait for logging to complete
                    self._log.store_done.wait()
                    self._log.store_done.clear()
                    
                    
                    if self.user_data_request.is_set():
                        #: Copy to user data block
                        #: Don't try hard at all.  If either are busy
                        #: then do nothing. 
                        
                        if self.user_data.lock.acquire(False):
                            try:
                            
                                if self._acq.buffer.lock.acquire(False):
                                    try:
                                        
                                        #: We have both buffers
                                        self.user_data.numAverages = self._acq.buffer.numAverages
                                        self.user_data.fftdata     = self._acq.buffer.fftdata
                                        self.user_data.stats       = self._acq.buffer.stats

                                        #: Notify user that new data is available
                                        self.user_data_ready_event.set()
                                        
                                        #: Process user callback
                                        if self.on_user_data_ready:
                                            self.on_user_data_ready(self.user_data)

                                        #: Clear user request flag
                                        self.user_data_request.clear()
                                        
                                    finally:
                                        self._acq.buffer.lock.release()
                            
                            finally:
                                self.user_data.lock.release()
    

                    #: Release buffer back to acquisition thread
                    self._acq.buffer_release.set()   

                #: Execute heartbeat task
                if self._heartbeat_event.is_set():
                    self._heartbeat_event.clear()
                    if self.on_heartbeat_task:
                        self.on_heartbeat_task._execute()
                
                #: Handle commands 
                cmd = self._get_cmd()
                if cmd:
                    if cmd == 'stop':
                        
                        self._acq.send_command('stop')
                    else:
                        logger.warning('{0} ignored command {1} in state {2}'.format(self.__class__.__name__, cmd, self._state))
                    
                #: Wait for acquisition to complete
                if self._acq.stop_event.is_set():
                    self._acq.stop_event.clear()
                    self._state = 'acq_done'
                    logger.debug('Acquisition stop event')
                    self.stop_event.set()
                    self._log.send_command('stop')
                    
                    
                
                 
            elif self._state == 'acq_done':
                self._state = 'idle'
 
        self._terminate.clear()
        

    
        
        
        
        
    
    