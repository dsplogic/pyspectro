# ------------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
# ------------------------------------------------------------------------------


from atom.api import Atom, Property, Value, Str, Bool, Typed

#: Import comtypes and initialize in multithreading mode
#: Must set coinit_flags before importing
#sys.coinit_flags = 0x0 #:COINIT_MULTITHREADED     = 0x0
import sys
sys.coinit_flags = 0x2 #:COINIT_APARTMENTTHREADED = 0x2
import comtypes


from threading import Lock
import logging

from ..applib.AgMD2models import IAgMD2Ex3

logger = logging.getLogger(__name__)

AcquisitionMode = {
 'Normal'        : 0x00000000, # Selects normal digitizer mode 
 'UserFDK'       : 0x0000000F, # Selects user FDK mode. Requires model M9703B with FDK option. 
 'Averager'      : 0x00000001, # Selects averager mode. 
 'PeakDetection' : 0x00000002, # Selects peak detection mode. 
 'BaseBand0'     : 0x00000003 # Selects Base Band 0 acquisition mode.
} 

#: AgMD2VerticalCouplingEnum
InputCoupling = {
 'AC' : 0,
 'DC' : 1,
 'GND': 2                
}

def discoverChannels(instr):
    """ Discover channels

    Parameters
    ----------
    instr : AgMD2 object
        Digitizer instrument

    Returns
    -------
    channelDict : dict of str -> IAgMD2Channel Interface
        Mapping of channel names to channel interface objects

    """
    
    channelDict = dict()
    
    for k in range(instr.Channels.Count):
        
        name = instr.Channels.Name(k+1)
        
        obj = instr.Channels.Item(name)
        
        channelDict[name] = obj
        
    return channelDict

def discoverLogicDevices(instr):
    """ Discover logic devices

    Parameters
    ----------
    instr : AgMD2 object
        Digitizer instrument

    Returns
    -------
    fpgaDict : dict of str -> IAgMD2LogicDevice Interface
        Mapping of FPGA names to FPGA LogicDevice interface objects

    """
    fpgaDict = dict()

    #: qUERY IAgMD2LogicDevices Interface
    for k in range(instr.LogicDevices.Count):
        
        name = instr.LogicDevices.Name(k+1)
        
        obj = instr.LogicDevices.Item(name)
        
        fpgaDict[name] = obj
        
    return fpgaDict

def discoverMemoryBanks(instr):
    """ Discover memory banks attached to each logic device

    Parameters
    ----------
    instr : AgMD2 object
        Digitizer instrument

    Returns
    -------
    fpgaDict : dict [string1][string2] -> IAgMD2LogicDeviceMemoryBank
        Mapping of FPGA names and memory banks to Memory Bank Interface objects,
        where string1 is the logicDevice name (e.g. DPUA) and string2
        is the Memory name (e.g. DDRA) 

    """
    
    logicDevice = discoverLogicDevices(instr)
    
    result = dict()
    
    for deviceName, device in logicDevice.items():
        
        #: Query IAgMD2LogicDeviceMemoryBanks object for attached objects 
        result[deviceName] = dict()
        
        for k in range(device.MemoryBanks.Count):
            
            bankName = device.MemoryBanks.Name(k+1)
            
            obj = device.MemoryBanks.Item(bankName)
            
            result[deviceName][bankName] = obj
            
    return result


def read_memory(instr, logicDevice, memoryBank, length):
    
    try:
        memoryBank = instr.LogicDevices2.Item[logicDevice].MemoryBanks.Item[memoryBank]
        
    except Exception as e:
        
        raise Exception('Cannot access memory bank %s:%s due to the following error %s' % (logicDevice, memoryBank, str(e)))



class AgMD2Device(Atom):
    """ Device driver for an FDK-Enabled AgMD2 device
    
    This is the base class for the AgMD2Digitizer
    """

    #: resourceName : str
    #:     The resource name used to connect to instrument,
    #: such as 'PXI4::4-0.0::INSTR'.  This property must be set
    #: prior to calling the connect() method.
    resourceName = Str()

    #: bitfile : str
    #:     Name of the bitfile used to define the instruments 
    #: behavior.  Bitfiles must be located in the AGMD2 driver
    #: firmware directory, e.g.:
    #: C:\Program Files (x86)\IVI Foundation\IVI\Drivers\AgMD2\Firmware
    bitfile = Str()

    #: isConnected : bool    
    #:     A read only propety indicating whether or not the driver
    #: is connected to the instrument.
    isConnected = Property()

    #: instrument : comtypes.IUnknown
    #:     Provides public access to the instruments AgMD2 COM interface. 
    #: This object is only valid when the instrument is connected.  Otherwise
    #: the value is None.
    instrument = Typed(comtypes.IUnknown)  
    
    #: model :  IAgMD2Ex3 (* Not currently used *)
    #:     An application utility (helper) model (use is optional)
    #: This object provides a model of device parameters that can be used
    #: by a higher-level application.  It includes local storage for device 
    #: parameters and a mechanism to update/apply them through the COM
    #: interface.  Local storage is provided by Atom.Member objects that can
    #: be bound to an Enaml View to create a GUI application. The attributes 
    #: of this object closely mirror those of the 'instrument' object.  
    #: Care must be taken to only modify model parameters (Members) from the 
    #: main GUI thread.  In the case of Enaml, this is done using the 
    #: 'deferred_call()' mechanism.
    #: This object is only valid when the instrument is connected.  Otherwise
    #: the value is None.
    #model = Typed(IAgMD2Ex3)

    #: The following are convenience properties to provide Pythonic 
    #: access to repeated resources found through discovery.  The objects
    #: are exposed in a dictionary with names as dictionary keys.
    channel     = Property(cached=True) #: Dict of IAgMD2Channel
    logicDevice = Property(cached=True) #: Dict of IAgMD2LogicDevice
    memoryBank  = Property(cached=True) #: Dict of IAgMD2LogicDeviceMemoryBank
    options     = Property(cached=True)
    
    #: Thread lock for protecting driver access to AgMD2Device.instrument
    #: The lock can be acquired/released externally using 
    #: AgMD2Device.lock.acquire() and AgMD2Device.lock.release()
    #: Accesses to AgMD2Device.instrument from multiple threads should be managed
    #: externally as required.
    lock = Value(factory=Lock)

    
    def _get_isConnected(self):
        
        if self.instrument:
            if self.instrument.Initialized:
                return True
        
        return False
    
    def _get_options(self):
        
        if self.isConnected:
        
            optionstring = self.instrument.InstrumentInfo.Options
            
            return optionstring.split(',')
            
    
    def connect(self):
        """ Connect to device 
        
        Returns
        -------
            boolean: True if connection was successful
             
        """
        #with self.lock:
            
        if not(self.isConnected):
        
            logger.info('Connecting to %s...' % self.resourceName)
    
            try:        
                      
                self.instrument = comtypes.client.CreateObject("AgMD2.AgMD2")
                
                #: Compute Initialization strings
                initstring = self._getInitializationString()
        
                #: Initialize Device
                self.instrument.Initialize(self.resourceName, 0, 0, initstring)
    
            except Exception as e:
                
                logger.info('Connection attempt failed with error: %s ' % str(e))
                
                return False
                
            logger.info('Connected to %s'  % self.resourceName)

            #: Set to FDK mode if a bitfile was used
            if self.bitfile:
                
                self.instrument.Acquisition.Mode = AcquisitionMode['UserFDK']
                
            #: Apply variable settings
            self.instrument.Acquisition.ApplySetup()   
            
            logger.info("Instrument ready")
            
            return True
        

    def disconnect(self):
        """ Disconnect from instrumnet 
        The primary purpose of this function is to destroy links to digitizer driver objects 
        to facilitate garbage collection
        
        In addition, the cached properties must be reset (i.e. cleared) so that upon reconnection,
        resources will be re-discovered.
        """
        if not self.instrument:
            logger.info('Instrument already disconnected')
            return
        
        if not self.instrument.Initialized:
            logger.info('Instrument already disconnected')
            return

        #with self.lock:
            
        #: Clear resource dictionaries and reset cached properties 
        self.channel.clear()
        self.members()['channel'].reset(self)
        
        self.logicDevice.clear()
        self.members()['logicDevice'].reset(self)
        
        self.memoryBank.clear()
        self.members()['memoryBank'].reset(self)
        
        #: Destroy spplication utility model to release resources
        #self.model.destroy()
        #self.model = None

        #: Close and clear instrument to release driver
        self.instrument.close()
        self.instrument = None
                
        logger.info('Disconnected')
                

    def calibrate(self, force = False):
        """ Calibrate the instrument (if necessary)
        
        Parameters
        ----------
        force: bool
            Set to true to force a calibration
        """
        result = None
        
        if self.instrument.Calibration.IsRequired:
            logger.info('Calibrating instrument...')
            result = self.instrument.Calibration.SelfCalibrate()
            logger.info('Calibration complete.')
        
        return result

    def _getInitializationString(self):

        """ Setup initializtion strings
        
        """
        initString = []
                
        #: Option Strings
        initString.append('Simulate=false')
       
        #: Followed by Driver Setup Parameters
        initString.append('DriverSetup=MODEL=u5303A') 
        
        #: Disable calibration
        initString.append('CAL=0') 
        
        initString.append('Trace=false')
        
        if self.bitfile:
            customBitfile = '='.join(['UserDpuA',self.bitfile])
            initString.append(customBitfile)    

        return ",".join(initString)
    
    
    """ Resource discovery methods
    
    """
    def _get_channel(self):
        
        return discoverChannels(self.instrument)        

    def _get_logicDevice(self):
        
        return discoverLogicDevices(self.instrument)        
            
    def _get_memoryBank(self):

        return discoverMemoryBanks(self.instrument)        

    def __del__(self):
        #print('DELETING: Digitizer')
        if self.isConnected:
            self.disconnect()
        #print('DELETED: Digitizer')

        
class Digitizer(AgMD2Device):
    """ Base driver for digitizer
    
    """

    #: interleaving Property 
    interleaving = Property()
    
    def _set_interleaving(self, val):
        if self.isConnected:
            #with self.lock:
            if bool(val):
                self.channel['Channel1'].TimeInterleavedChannelList = 'Channel2'
            else:
                self.channel['Channel1'].TimeInterleavedChannelList = ''
        else:
            logger.warning('Warning: cannot set interleaving property')
    
    def _get_interleaving(self):
        if self.isConnected:
            #with self.lock:
            if self.channel['Channel1'].TimeInterleavedChannelList == 'Channel2':
                return True
            elif self.channel['Channel1'].TimeInterleavedChannelList == '':
                return False
            else:
                raise Exception('Device has invalid interleaving setting')
        else:
            return None
            

    def connect(self):
        """ A re-implemented connect method
        
        Additionally set properties defined in this class
        
        """
        
        success = super(Digitizer, self).connect()
        
#         if success:
#              
#             #: Reapply settings
#             self._set_interleaving(self.interleaving)
        
        return success
        

    def startProcessing(self, processingType = 1):
        
        #: Make sure instrument is calibrated
        self.calibrate(force= False)
                
        #: Sent start processing command to DSP core
        self.instrument.Acquisition.UserControl.StartProcessing(processingType)

        return True
    
    def stopProcessing(self, processingType = 1):
        
        #: Sent start processing command to DSP core
        self.instrument.Acquisition.UserControl.StopProcessing(processingType)

                
class ConfigurationStore(Atom):
    """ Interface to the IVI configuration store
    
    A programmatic interface to communicating with the IVI onfiguration store
    
    C:\ProgramData\IVI Foundation\IVI\IviConfigurationStore.xml
    
    It creates a connection to:
        C:\Program Files\IVI Foundation\IVI\Bin\IviConfigServer.dll
        C:\Program Files\IVI Foundation\IVI\Lib_x64\msc\IviConfigServer.lib

    """
    
    _store   = Value()
    
    def __init__(self, *args, **kwargs):
        super(ConfigurationStore,self).__init__(*args, **kwargs)
        
        self._store = comtypes.client.CreateObject("IviConfigServer.IviConfigStore.1")


