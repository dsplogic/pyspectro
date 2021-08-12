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
import time
import numpy as np
from atom.api import Atom, Int, Enum, Value, Typed, Bool, observe, Float, Tuple, Signal, Str, FloatRange
from enaml.application import deferred_call, Application
from pyspectro.common.console import ConsoleTextWriter 
from pyspectro.applib.core import PySpectroCore    
from pyspectro.applib.processor import TimedProcessor
from pyspectro.applib.instrument_props import get_instrument_properties, get_slow_properties, get_temperature_properties
from .mpl_figure import SpectrumFigure
from .cwtest_model import CwTestModel

import logging
from pyspectro.applib.processor import ProcessTask
import pyspectro.apps

logger = logging.getLogger(__name__)

def apply_updated_temperatures(model, temperatures):
    
    model.temperatures.temp_ch1_c       = temperatures['temp_ch1_c']
    model.temperatures.temp_ch1_c_max   = temperatures['temp_ch1_c_max']
    model.temperatures.temp_ch2_c       = temperatures['temp_ch2_c']
    model.temperatures.temp_ch2_c_max   = temperatures['temp_ch2_c_max']
    model.temperatures.temp_adc_c       = temperatures['temp_adc_c']
    model.temperatures.temp_adc_c_max   = temperatures['temp_adc_c_max']

    #: Board Temperatures
    model.temperatures.temp_board_c     = temperatures['temp_board_c']
    model.temperatures.temp_board_c_max = temperatures['temp_board_c_max']
    model.temperatures.temp_dpu_c       = temperatures['temp_dpu_c']
    model.temperatures.temp_dpu_c_max   = temperatures['temp_dpu_c_max']


def handle_heartbeat_task_result(model, result):
    """ Heartbeat result handler 
    
    This function must be executed on main GUI thread using a deferred_call.
    
    Parameters
    ----------
    result: dict
        Result of heartbeat_task
    """

    apply_updated_temperatures(model, result)

    model.Calibration_IsRequired = result['Calibration_IsRequired']
    
    model.SampleRate = result['SampleRate']
    model.Nfft = result['Nfft']
    model.downsample_ratio = result['downsample_ratio']
    
    #: The following are manually applied
    #model.inputSettings.voltageOffset = result['Ch1_Offset']
    #model.inputSettings.FilterBypass  = result['Ch1_FilterBypass']
    #model.inputSettings.voltageRange  = result['Ch1_Range']
    
    
def heartbeat_task(model):
    """ Heartbeat task scheduled/executed by pyspectro core
    
    This task should perform limited processing to avoid delaying the core
    task loop.
    """
    with model.core.device.lock:
        
        #: Get properties
        result       = get_slow_properties(model.core.device)
        temperatures = get_temperature_properties(model.core.device)
        result.update( temperatures )
        
        
    deferred_call(handle_heartbeat_task_result, model, result)
        

class InstrumentProperties(Atom):
    """ Container for read-only system properties
    
    """
    Instrument_IOVersion          = Value()
    Instrument_SerialNumberString = Value()
    Instrument_Options            = Value()
    Instrument_NbrADCBits         = Value()
    Instrument_Model              = Value()
    Instrument_FirmwareRevision   = Value()
    Driver_Identifier             = Value()
    Driver_Revision               = Value()
    Driver_IoResourceDescriptor   = Value()
    license_ok                    = Value()
    
class Temperatures(Atom):
    

    #: Channel temperatures (all are identical)        
    temp_adc_c       = Float()
    temp_adc_c_max   = Float()
    temp_ch1_c       = Float()
    temp_ch1_c_max   = Float()
    temp_ch2_c       = Float()
    temp_ch2_c_max   = Float()

    #: Board Temperatures (all are identical)
    #: Max allowable is 85 deg C.
    temp_board_c     = Float()
    temp_board_c_max = Float()
    temp_dpu_c       = Float()
    temp_dpu_c_max   = Float()

    
class InputSetting(Atom):
    voltageOffset  = FloatRange()
    voltageRange   = Enum(1.0, 2.0)
    FilterBypass   = Bool()
    
    
class SpectroModel(Atom):

    Nfft         = Int() 
    
    SampleRate   = Float()
    
    complexData = Bool()
    
    interleaved  = Bool()
    
    inputSettings = Typed(InputSetting, ())
    
    instrumentProperties = Typed(InstrumentProperties, ())
    
    temperatures = Typed(Temperatures, ())

    refresh_timer = Typed(TimedProcessor) 
    
    enable_data_logging = Bool(False)
    
    downsample_ratio = Int(1)
    
    core = Typed(PySpectroCore)
    core_state         = Enum('disconnected','connecting','idle','acq_start','acquiring','acq_done')

    #: Main graph display
    spectrumFigure      = Typed(SpectrumFigure,())

    #: Acquisition        
    processLock         = Value(factory=threading.Lock)
    guiProcessDropped   = Int()
    
    #: UHSFFTS Properties
    acquisitionMode = Enum('One-shot', 'Continuous')
    numAverages     = Int(6104) #: 100 msec
    disablePolyphase = Bool(False)
    memoryError      = Bool(False)
    dspOverflow      = Bool(False)   
    dspCoreActive    = Bool()

    #: Connection Properties
    connectionSignal   = Signal()

    #: Application properties/settings
    cwTestModel = Typed(CwTestModel)    

    #: Raw device properties    
    #offsets        = Tuple()
    #channelEnabled = Tuple(item=bool)

    #: Console    
    console = Typed(ConsoleTextWriter, ())
    
    
    resourceName = Str()
    
    
    #: User acquisition Statistics
    nAcquisitions = Int()
    nMeasurements = Int() #: Number of measurements in prior acquisition
    nDropped      = Int() #: Number of measurements dropped
    nBlocked      = Int() #: Number of measurement transfers blocked
    
    #: Dispaly refresh interval in continuous acquisition
    refresh_interval = Float(0.1)
    
    Calibration_IsRequired = Bool()
    
    def __init__(self,*args, **kwargs):
        
        super(SpectroModel, self).__init__(*args, **kwargs)
        
        self.resourceName = 'PXI4::4-0.0::INSTR'
        
        
        
        #self.console.enable()

    def display_next_measurement(self):
        """ Request data update from core, initiating figure redraw
        
        This function initiates the following sequence of events:
        
            - Assert core.user_data_request
            - On *next* measurement event
                - core updates core.user_data buffer
            - core asserts core.user_data_ready_event (this event not used)
            - core initiates on_user_data_ready callback (self.processDataInUiCallback)
            - processDataInUiCallback issues deferred_call to execute self.process_data_in_gui on main GUI thread
            - self.process_data_in_gui issues .redraw() on figure
            
        """
        #:logger.debug('REQUESTING DISPLAY UPDATE')
        self.core.user_data_request.set()

    @observe('disablePolyphase')
    def _disablePolyphase_handler(self, change):
        with self.core.device.lock:
            self.core.device.disablePolyphase = change['value']        

    @observe('enable_data_logging')
    def _enable_data_logging_handler(self, change):
        """ This event is restricted to happening when device is idle or disconnected 
        
        """
        with self.core.device.lock:
            self.core.enable_data_logging = change['value']        

    @observe('downsample_ratio')
    def _downsample_ratio_handler(self, change):

        with self.core.device.lock:
            
            if change['value'] == 1:
                
                self.core.device.downsample_ratio = 1
                
            elif change['value'] == 2:

                self.core.device.downsample_ratio = 2

            else:
                logger.warning('Invalid demiation ratio selected: {}'.format(change['value']))
        
        #: Update model and spectrometer plot with sample rate from Spectrometer
        self.SampleRate = self.core.device.sampleRate
        self.spectrumFigure.sampleRate = self.SampleRate
        self.spectrumFigure.update_xrange()
                
    def _on_core_state_change(self, state):
        """ State change callback 
        
        A callback executed in the core thread when the core state changes
        A deferred_call is used to ensure that model is updated on the
        main GUI thread.
        """
        deferred_call(setattr, self, 'core_state', state)
        
    @observe('core_state')
    def _core_state_change_handler(self, change):
        """ Local handler to react to changes in core state
        
        """

        if change['type'] != 'update':
            return

        newval = change['value']
        

        logger.debug('core_state changed from {0} to {1}'.format(change['oldvalue'], newval))
            
        if newval == 'connecting':
            pass

        
        elif newval == 'disconnected':
            
            if change['oldvalue'] == 'idle':
            
                #: This change should occur as the result of a sucessfull call
                #: to core.disconnect.  There is no need to wait for 
                #: core.disconnect_event.

                #: Signal GUI to close windows
                self.connectionSignal(False)
                
                self.core = None
                self.cwTestModel = None
                
                self.refresh_timer.stop()
                self.refresh_timer = None
                
            elif change['oldvalue'] == 'connecting':
                #: result of a failed connection
                pass

        
        elif newval == 'idle':
            
            
            if change['oldvalue'] == 'connecting':
                
                #: Changinf from connecting to idle:
                
                #: Read device properties
                with self.core.device.lock:
                    
                    result = get_instrument_properties(self.core.device)

                #: Apply to model                    
                self.instrumentProperties.Instrument_IOVersion        = result['Instrument_IOVersion']
                self.instrumentProperties.Instrument_SerialNumberString = result['Instrument_SerialNumberString']
                self.instrumentProperties.Instrument_Options          = result['Instrument_Options']           
                self.instrumentProperties.Instrument_NbrADCBits       = result['Instrument_NbrADCBits']        
                self.instrumentProperties.Instrument_Model            = result['Instrument_Model']             
                self.instrumentProperties.Instrument_FirmwareRevision = result['Instrument_FirmwareRevision']  
                self.instrumentProperties.Driver_Identifier           = result['Driver_Identifier']            
                self.instrumentProperties.Driver_Revision             = result['Driver_Revision']              
                self.instrumentProperties.Driver_IoResourceDescriptor = result['Driver_IoResourceDescriptor']  
                self.instrumentProperties.license_ok                  = result['license_ok']  

                #: Get properties from device
                self.refreshProperties()

                #: Initialize spectrumFigure and update X axis
                self.spectrumFigure.numAverages = self.numAverages
                self.spectrumFigure.sampleRate = self.SampleRate
                self.spectrumFigure.Nfft = self.Nfft
                self.spectrumFigure.complexData = self.complexData
                self.spectrumFigure.sampleRate = self.SampleRate
                
                self.spectrumFigure.update_xrange()
                 
                self.cwTestModel = CwTestModel(self.core.device)
                
                #: Force defaults properties
                self.inputSettings.voltageRange = 1.0
                
                #: Apply 
                self.applyProperties()
                
                #: Initialize timer thread to to update measurement (deferred to GUI thread)
                self.refresh_timer = TimedProcessor(interval = self.refresh_interval, 
                                                    task = deferred_call, 
                                                    args = (self.display_next_measurement,), 
                                                    kwargs = {})
                
                #: Reset user stats
                self.nAcquisitions = 0
                self.nMeasurements = 0
                self.nDropped = 0
                self.nBlocked = 0

                
                #: Signal GUI to open windows
                self.connectionSignal(True)
                
            elif change['oldvalue'] == 'acq_done':
                """ Acquisiton completed
                
                This state can occur automatically at the end of a one-shot acquisition, or
                as the result of a stopCommand issued during a continuous acquisition
                """
                #: Get properties from device
                self.refreshProperties()
                
                logger.info('Acquisition {0} complete'.format(self.nAcquisitions))

            
        
        elif newval == 'acq_start':
            pass

        elif newval == 'acquiring':
            pass

        elif newval == 'acq_done':
            pass
        else:
            raise Exception('Unknown state {0}'.format(newval))


                            
    def startAcquisition(self):
        """ Start acquisitionn (one-shot or continuous mode)
        
        """
        if self.core_state != 'idle':
            logger.info('Cannot start acquisition, instrument is in {0} state'.format(self.core_state))
            return
        
        with self.core.device.lock:
            self.core.device.numAverages = self.numAverages
            
        self.spectrumFigure.numAverages = self.numAverages
        self.spectrumFigure.sampleRate = self.SampleRate
        
        #: If one-shopt acquisition, request display of next measurement
        #: Otherwise, rely on GUI timer to update measurement
        if self.acquisitionMode == 'One-shot':
            self.display_next_measurement()
        else:
            #: Issue display_next_measurement from refresh thread
            self.refresh_timer.start()
        
        self.core.send_command('start')

        self.nMeasurements = 0
        self.nDropped = 0
        self.nBlocked = 0
        self.nAcquisitions += 1
        
        logger.info('Acquisition {0} started'.format(self.nAcquisitions))
        
    def stopAcquisition(self):
        """ Stop Acquisition
        
        This method shoudld be called when acquiring in continuous more to stop processing.
        """

        if self.core_state != 'acquiring':
            logger.warning('Cannot stop acquisition, instrument is in {0} state'.format(self.core_state))
            return

        #: Disable refresh thread
        self.refresh_timer.stop()
        
        #: Send stop command to core
        self.core.send_command('stop')


    def processDataInUiCallback(self, result):
        """ Notification callback 
        
        A callback executed in the core worker thread after data has been
        read from the device.  Since this is executed in the worker thread,
        care must be taken to update the model in the main GUI thread.
        
        Processing is delegated to the main GUI thread using 
        a deferred_call.
        
        A prcessLock is used to prevent repeated calls from overflowing
        the Application task heap.
        """
        
        #logger.debug('Running processDataInUiCallback for measurement {0}'.format(result.stats.Nmsr_total))
        
        #app = Application.instance()
        #pending = app._qapp.hasPendingEvents()
        #logger.debug('Acq handler: Qapp pending events=%s' % pending)
        
        #logger.debug("Nmsr_total %s.  Missed: %s" % (result.Nmsr_ok, result.Nmsr_drop))  
 
        #: Don't fetch/process data if refresh is disabled
            
        #: If prior processing is completed, initiate another event
        if self.processLock.acquire(False):
            
            try: 
                if not self.spectrumFigure.disableRefresh:
                    #: Post event to Qt main event loop
                    deferred_call(self.process_data_in_gui, result )
                    
                else:    
                    deferred_call(self.process_stats_only_in_gui, result)      
                    
            finally:            
                
                self.processLock.release()
                
        else:
            #: Lock unavaliable, drop event
            self.guiProcessDropped = self.guiProcessDropped + 1
            
            logger.debug('GUI Data processing blocked: %s'  % self.guiProcessDropped)  

    def process_data_in_gui(self, result):
        """ Process spectrum data
        
        Process data on the main GUI thread.  Should only be called using deferred_call
        """
        logger.debug('Processing measurement {0}'.format(result.stats.Nmsr_total))

        app = Application.instance()
        app._qapp.processEvents()
        logger.debug('Pending events: = %s' % app._qapp.hasPendingEvents())

        with self.processLock:
            
            #: Update figure properties from model
            self.spectrumFigure.numAverages = self.numAverages
            self.spectrumFigure.voltageRange = self.inputSettings.voltageRange
            
            self.spectrumFigure.ax.grid(True)
            self.spectrumFigure.ydata = result.fftdata
            self.spectrumFigure.redraw()
    
            self.nMeasurements = result.stats.Nmsr_total
            self.nDropped      = result.stats.Nmsr_drop
            self.nBlocked      = result.stats.Nmsr_blocked

    def process_stats_only_in_gui(self, result):
        """ Update stats
        
        Update data statistics the main GUI thread.  Use when plot refresh is disabled  
        Should only be called using deferred_call
        """

        with self.processLock:
            
            #: Update figure properties from model
            self.nMeasurements = result.stats.Nmsr_total
            self.nDropped      = result.stats.Nmsr_drop
            self.nBlocked      = result.stats.Nmsr_blocked


    def setContinuousMode(self, value):

        if self.core_state != 'idle':
            logger.warning('Cannot update continuous mode, instrument is in {0} state'.format(self.core_state))
            return
            
        with self.core.device.lock:
            
            self.core.device.continuousMode = value
            
            if value:
                self.acquisitionMode = 'Continuous'
            else:
                self.acquisitionMode = 'One-shot'


    def connect(self, app_Nfft, channels):
        """ Initiate a connection
        
        Parameters
        ----------
        app_Nfft : int
            FFT Size
            
        channels : int
            1 : Single channel, real FFT  (interleaving on)
            2 : Two channels, complex FFT (interleaving off)
        
        """
        #: Get application to load into spectrometer
        logger.info('Requested FFT Size: {}'.format(app_Nfft))
            
        app = pyspectro.apps.get_application(app_Nfft, channels)
        
        if not app:
            
            logger.error('Application not found, FFT Size: {}'.format(app_Nfft))
            logger.error('PySpectroCore initialization failed.')
            
            return

        
        if not self.core:
            
            #: Instantiate Core
            self.core = PySpectroCore(app)
            logger.debug('PySpectroCore Created')
            
            #: Assign callback when state changes
            self.core.on_state_change= self._on_core_state_change
            logger.debug('Assigned state change callback')
    
            self.core.on_user_data_ready =  self.processDataInUiCallback

            self.core.on_heartbeat_task = ProcessTask(heartbeat_task, (self,), {})
            
        logger.debug('Connecting to resource {}'.format(self.resourceName))
        self.core.connect(self.resourceName)
        
                
    def disconnect(self, blocking= False):
        """ Initiate a disconnect
        
        """
        
        if self.core:
            
            if self.core_state not in ('idle','disconnected'):
                self.stopAcquisition()
                
            
            if self.core_state == 'idle':

                self.core.disconnect()
                self.core.disconnect_event.wait()
                self.core.disconnect_event.clear()

                self.core.terminate()

            elif self.core_state == 'disconnected':
                pass
            
            else:
                
                logger.warning('Could not disconnect.  Device in state {0}'.format(self.core_state))

            
        
    def applyProperties(self):
        
        if self.core_state == 'idle':

            with self.core.device.lock:
                
                self.core.device.instrument.Channels['Channel1'].Offset = self.inputSettings.voltageOffset 
                self.core.device.instrument.Channels['Channel1'].Range = self.inputSettings.voltageRange
                self.core.device.instrument.Channels['Channel1'].Filter.Bypass = self.inputSettings.FilterBypass 

                self.core.device.instrument.Channels['Channel2'].Offset = self.inputSettings.voltageOffset 
                self.core.device.instrument.Channels['Channel2'].Range = self.inputSettings.voltageRange
                self.core.device.instrument.Channels['Channel2'].Filter.Bypass = self.inputSettings.FilterBypass 

                self.core.device.instrument.Acquisition.ApplySetup()
            
        else:
            
            logger.warning('Could not apply properties - Instrument in {0} state'.format(self.core_state))

    def refreshProperties(self):
         
        if self.core_state == 'idle':
 
            with self.core.device.lock:
                 
                self.Nfft         = self.core.device.Nfft
                self.interleaved  = self.core.device.interleaving
                self.complexData  = self.core.device.app.complexData
                self.SampleRate   = self.core.device.sampleRate
                
                self.inputSettings.voltageOffset = self.core.device.instrument.Channels['Channel1'].Offset
                self.inputSettings.voltageRange  = self.core.device.instrument.Channels['Channel1'].Range
                self.inputSettings.FilterBypass  = self.core.device.instrument.Channels['Channel1'].Filter.Bypass

                self.inputSettings.voltageOffset = self.core.device.instrument.Channels['Channel2'].Offset
                self.inputSettings.voltageRange  = self.core.device.instrument.Channels['Channel2'].Range
                self.inputSettings.FilterBypass  = self.core.device.instrument.Channels['Channel2'].Filter.Bypass
 
        else:
             
            logger.warning('Could not refresh properties - Instrument in {0} state'.format(self.core_state))



    
if __name__ == '__main__':
    
    
    obj = SpectroModel()
    
    try:
        obj.connect()
        
        obj.startAcquisition()
        
        time.sleep(5)
        
    finally:
        obj.disconnect()
    
    