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
from Queue import Queue

from atom.api import Atom, Typed, Enum, Value
from pyspectro.drivers.Spectrometer import Spectrometer

import logging
logger = logging.getLogger(__name__)

from .processor import CommandThread

class ConnectionManager(CommandThread):
    """ Threaded connection manager
    
    This object provides a non-blocking connection manager to allow
    the primary application to continue functioning while a connection
    is in progress.
    """

    _valid_commands = ['connect','disconnect']
    
    #: Command queue
    #command      = Value(factory = Queue)

    connected    = Typed(threading._Event, ())
    disconnected = Typed(threading._Event, ())

    connectionState = property(lambda self: self._state)
    
    #: State response queue
    status       = Value(factory = Queue)
    
    #: Private storage for worker thread
    #_thread       = Typed(threading.Thread)
    #_finish       = Typed(threading._Event, ())
    _state        = Enum('disconnected', 'connecting', 'connected', 'failed') 
    
    _device   = Typed(Spectrometer)
    
    def __init__(self, device):
        """ Initialize a Connection manager

        Parameters
        ----------
        device : Spectrometer
            Spectrometer driver

        """
        self._device = device
        
#     def initialize(self):
#         """ Create and start worker thread
#         
#         """
#         logger.debug('Initializing %s' % (self.__class__.__name__))
#         self._thread  = threading.Thread(target = self._worker)
#         self._thread.start()
        
    def connect(self):
        self.send_command('connect')

    def disconnect(self):
        self.send_command('disconnect')

#     def terminate(self):
#         """ Terminate worker thread and wait for it to terminate
#         
#         This method should be called prior to disconnecting the instrument.
#         """
#         if self._thread:
#             logger.debug('Terminating %s' % (self.__class__.__name__))
#             #: signal worker to finish processing
#             self._finish.set()
#             
#             #: Join worker thread
#             self._thread.join()
#             
#             self._thread = None

    def _main_loop(self):
        """ Connection state machine controller
        
        Main state machine that handles connection requests.
        This function relies on the driver to make the connect/disconnect commands thread safe.
        
        """

        #: Initialize comtypes for this thread using flags defined in sys.coinit_flags        
        import comtypes
        comtypes.CoInitializeEx()

        while not self._terminate.wait(0.1):
            
            if self._state   == 'disconnected':
                
                cmd = self._get_cmd()
                if cmd == 'connect':
                    self._state = 'connecting'
                    self.status.put('connecting')

                elif cmd == 'disconnect':
                    #: already disconnected
                    self.status.put('disconnected')
                    
            elif self._state == 'connecting':
                with self._device.lock:
                    result = self._device.connect()
                
                if result:
                    self.connected.set()
                    self._state = 'connected'
                    self.status.put('connected')
                else:
                    self._state = 'failed'
                    self.status.put('failed')
                
            elif self._state == 'connected':

                cmd = self._get_cmd()
                if cmd == 'disconnect':
                    with self._device.lock:
                        self._device.disconnect()
                    self.disconnected.set()
                    self._state = 'disconnected'
                    self.status.put('disconnected')
                    
                elif cmd == 'connect':
                    pass
                
            elif self._state == 'failed':
                self._state = 'disconnected'
                self.status.put('disconnected')
            
            
        self._terminate.clear()

#     def _get_cmd(self):
#         """ Check for new command.
#         
#         Get command from queue.  Return empty string if queue is empty.
#         """
#         try:
#             cmd = self.command.get(False)
#         except:
#             cmd = ''
#             
#         if cmd not in ['', 'connect', 'disconnect']:
#         
#             msg = 'Invalid command received: %s' % cmd
#             logger.error(msg)
#             raise Exception(msg)
#         
#         if cmd:
#             logger.debug('Received command: %s' % cmd)
#             
#         return cmd

if __name__ == '__main__':
    pass
    
    