#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------

""" This module provides the data models used to represent a Digitizer.

The IAgMD2Ex3 provides storage for hierarchical digitizer parameters at the application level.
These attributes can be "applied" to the digitizer device or "updated" from the digitizer 
device using the Digitizer driver.

"""
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


 
from atom.api import Atom, Bool, Unicode, Enum, Typed, Int, Float, Callable, Value, Dict

from pyspectro.common.parameters import p_, child_
from pyspectro.common.comdevice import DeviceParameterModel, DeviceParameterContainerModel

    
class IAgMD2ChannelFilter(DeviceParameterModel):
    Bypass       = p_( Int() )
    MaxFrequency = p_( Float() )
    MinFrequency = p_( Float() )
    Configure    = p_(Value() )  #: method

class IAgMD2ChannelMeasurement(DeviceParameterModel):
    """ Not Implemented """
    pass

class IAgMD2ChannelMultiRecordMeasurement(DeviceParameterModel):
    """ Not Implemented """
    pass

class IAgMD2Channel(DeviceParameterModel):
    
    ConnectorName              = p_( Unicode() )
    Coupling                   = p_( Int() ) #Enum('AC', 'DC', 'GND')
    Enabled                    = p_( Bool() )
    InputConnectorSelection    = p_( Int() )
    InputImpedance             = p_( Float() )
    Offset                     = p_( Float(), writable=True )
    Range                      = p_( Float(), writable=True )
    Temperature                = p_( Float() )
    TimeInterleavedChannelList = p_( Unicode(), writable=True )

    Filter                 = child_( Value(factory= IAgMD2ChannelFilter) )
    Measurement            = child_( Value(factory= IAgMD2ChannelMeasurement) )
    MultiRecordMeasurement = child_( Value(factory= IAgMD2ChannelMultiRecordMeasurement) )

class IAgMD2Channels(DeviceParameterContainerModel): 
    childFactory = Callable(IAgMD2Channel) 
        
class IAgMD2AcquisitionStatus (DeviceParameterModel):
    """
        0x00000001 The digitizer is currently in the queried state. 
        0x00000002 The digitizer is not currently in the queried state. 
        0x00000003 The driver cannot query the instrument to determine if the digitizer is in the queried state.
    """
    IsIdle              = p_(Int())
    IsMeasuring         = p_(Int())
    IsWaitingForTrigger = p_(Int())
    #:IsWaitingForArm   = p_(Bool()) #: Not supported

class IAgMD2AcquisitionUserControl(DeviceParameterModel):
    """ IAgMD2AcquisitionUserControl
    
    TODO: Interface not complete (not in use)
    """
    TriggerSelection   = p_(Int())
    
    
class IAgMD2Acquisition(DeviceParameterModel):
    """IAgMD2Acquisition
    
    """
    MaxFirstValidPointValue = p_( Value() ) #: long type
    MaxSamplesPerChannel    = p_( Value() ) #: long type
    MinRecordSize           = p_( Value() ) #: long type
    Mode                    = p_(Int())
    NumAcquiredRecords      = p_( Value() ) #: long type
    NumRecordsToAcquire     = p_( Value() ) #: long type
    RecordSize              = p_( Value() ) #: long type
    SampleRate              = p_(Float())
    Status                  = child_(Value(factory = IAgMD2AcquisitionStatus))
    TimeInterleavedChannelListAuto = p_(Bool())
    UserControl             = child_(Value(factory = IAgMD2AcquisitionUserControl))
    

class IAgMD2Temperature(DeviceParameterModel):
    BoardTemperature  = p_( Float() )
    Units  = p_( Int() )

class IIviDriverIdentity(DeviceParameterModel):
    Description                = p_( Unicode() )
    GroupCapabilities          = p_( Unicode() )
    Identifier                 = p_( Unicode() )
    InstrumentFirmwareRevision = p_( Unicode() )
    InstrumentManufacturer     = p_( Unicode() )
    InstrumentModel            = p_( Unicode() )
    Revision                   = p_( Unicode() )
    SpecificationMajorVersion  = p_( Int() )
    SpecificationMinorVersion  = p_( Int() )
    SupportedInstrumentModels  = p_( Unicode() )
    Vendor                     = p_( Unicode() )

class IAgMD2MonitoringValue(DeviceParameterModel):  
    CurrentValue  = p_( Float() )
    LimitHigh     = p_( Float() )
    LimitLow      = p_( Float() )
    Unit          = p_( Unicode() )


class IAgMD2LogicDeviceMemoryBank(DeviceParameterModel):
    AccessControl    = p_(Int())
    AccessMode       = p_(Int())
    FIFOModeEnabled  = p_(Bool())

class IAgMD2LogicDeviceMemoryBanks(DeviceParameterContainerModel):
    childFactory = Callable(IAgMD2LogicDeviceMemoryBank)
    
class IAgMD2LogicDeviceIFDL(DeviceParameterModel):
    Enabled   = p_(Bool())
    IsActive  = p_(Bool())
 
 
class IAgMD2LogicDeviceIFDLs(DeviceParameterContainerModel):
    childFactory = Callable(IAgMD2LogicDeviceIFDL)


class IAgMD2LogicDevice(DeviceParameterModel):  
    FirmwareStoreCount  = p_(Int())
    SamplesUnsigned     = p_(Bool())
    
    #: 0: In Acquisition mode, the LogicDevice receives actual values from the ADC. This is the default mode.
    #: 1: In Emulation mode, the LogicDevice receives the values that have been uploaded to each stream using WriteStreamWaveformInt16().
    StreamMode          = p_(Int())
    
    StreamsCount        = p_(Int())
    MemoryBanks         = child_(Value(factory = IAgMD2LogicDeviceMemoryBanks))
    IFDLs               = child_(Value(factory = IAgMD2LogicDeviceIFDLs))

class IAgMD2LogicDevices(DeviceParameterContainerModel): 
    childFactory = Callable(IAgMD2LogicDevice)
     
class IAgMD2MonitoringValues(DeviceParameterContainerModel):  
    childFactory = Callable(IAgMD2MonitoringValue)


class IAgMD2InstrumentInfo(DeviceParameterModel):  
    #ChassisNumber       = p_(Int())  #: Not supported on platform.  TODO: handle non-supported parameters
    IOVersion           = p_(Unicode())
    NbrADCBits          = p_(Int())
    Options             = p_(Unicode())
    SerialNumberString  = p_( Unicode() )
    MonitoringValues    = child_(Value(factory = IAgMD2MonitoringValues) )

class IAgMD2SampleClock(DeviceParameterModel):  
    ExternalDivider     = p_( Float() )
    ExternalFrequency   = p_( Float() )
    OutputEnabled       = p_( Bool() )
    Source              = p_( Int() ) #: 0x00000000 Internal 1 External

class IAgMD2DelayControl(DeviceParameterModel):   
    Max   = p_(Int())
    Min   = p_(Int())
    Range = p_(Int())
    Range = p_(Int())

class IAgMD2DelayControls(DeviceParameterContainerModel):  
    childFactory = Callable(IAgMD2DelayControl)
    
class IAgMD2Calibration(DeviceParameterModel):   
    IsRequired    = p_(Bool())
    DelayControls = child_(Value(factory= IAgMD2DelayControls)) 

    #:SelfCalibrate = m_(Value())

class IAgMD2ControlIO(DeviceParameterModel):   
    AvailableSignals   = p_(Unicode())
    Signal             = p_(Unicode())
    
class IAgMD2ControlIOs(DeviceParameterContainerModel):  
    childFactory = Callable(IAgMD2ControlIO)

class IIviDriverOperation(DeviceParameterModel):
    Cache                 = p_(Bool())   
    DriverSetup           = p_(Unicode())   
    InterchangeCheck      = p_(Bool()) 
    IoResourceDescriptor  = p_(Unicode())
    LogicalName           = p_(Unicode())
    QueryInstrumentStatus = p_(Bool())
    RangeCheck            = p_(Bool())
    RecordCoercions       = p_(Bool())
    Simulate              = p_(Bool())

class IAgMD2ReferenceOscillator(DeviceParameterModel):
    ExternalFrequency = p_(Float())
    OutputEnabled      = p_(Bool())
    #: Source:
    #: AgMD2ReferenceOscillatorSourceInternal 0x00000000 The internal reference oscillator is used. 
    #: AgMD2ReferenceOscillatorSourceExternal 0x00000001 An external reference oscillator is used. 
    #: AgMD2ReferenceOscillatorSourceAXIeClk100 0x00000004 The AXIe backplane reference oscillator is used. 
    Source            = p_(Int())

class IAgMD2TriggerEdge(DeviceParameterModel):
    """ Slope
    AgMD2TriggerSlopeNegative 0x00000000 A negative (falling) edge passing through the trigger level triggers the digitizer. 
    AgMD2TriggerSlopePositive 0x00000001 A positive (rising) edge passing through the trigger level triggers the digitizer. 
    """
    Slope   = p_(Int())

 
class IAgMD2TriggerSourceMagnitude(DeviceParameterModel):
    pass
    """ DwellTimeSamples
    Positive values of dwell time indicate the number of samples that must be in 
    the initial trigger state (e.g. below the low threshold for a rising edge 
    trigger) before a trigger will be recognized. Negative values of dwell time 
    indicate the number of samples that must be in the second trigger state 
    before a trigger is recognized.
    """
    #:DwellTimeSamples = p_(Int()) NOT SUPPORTED

    """ Slope
    AgMD2TriggerSlopeNegative 0x00000000 A negative (falling) edge passing through the trigger level triggers the digitizer. 
    AgMD2TriggerSlopePositive 0x00000001 A positive (rising) edge passing through the trigger level triggers the digitizer. 
    """
    #Slope = p_(Int())  NOT SUPPORTED

class IAgMD2TriggerSource(DeviceParameterModel):   

    """ Coupling    
    AgMD2TriggerCouplingAC 0x00000000 The digitizer AC couples the trigger signal. 
    AgMD2TriggerCouplingDC 0x00000001 The digitizer DC couples the trigger signal. 
    AgMD2TriggerCouplingNoiseReject 0x00000004 The digitizer filters out the noise from the arm signal. 
    AgMD2TriggerCouplingHFReject 0x00000002 The digitizer filters out the high frequencies from the arm signal. 
    AgMD2TriggerCouplingLFReject 0x00000003 The digitizer filters out the low frequencies from the arm signal.
    """ 
    Coupling    = p_(Int())
    
    Edge        = child_(Value(factory = IAgMD2TriggerEdge ))
    
    """ Hysteresis
    Specifies the trigger hysteresis in Volts.
    """
    Hysteresis = p_(Float())
    
    """ Level
    Specifies the voltage threshold for the trigger sub-system. The units are Volts. 
    This attribute affects instrument behavior only when the Trigger Type is set to 
    one of the following values: Edge Trigger, Glitch Trigger, or Width Trigger. This 
    attribute, along with the Trigger Slope, Trigger Source, and Trigger Coupling attributes,
    defines the trigger event when the Trigger Type is set to Edge Trigger.
    """
    Level  = p_(Float())
    
    Magnitude   = child_(Value(factory = IAgMD2TriggerSourceMagnitude))
    
    """ Type
    AgMD2TriggerEdge 0x00000001 Configures the digitizer for edge triggering. An edge trigger occurs when the trigger signal specified with the Trigger Source attribute passes the voltage threshold specified with the Trigger Level attribute and has the slope specified with the Trigger Slope attribute. 
    AgMD2TriggerWidth 0x00000002 Configures the digitizer for width triggering. Use the IviDigitizerWidthTrigger extension properties and methods to configure the trigger. 
    AgMD2TriggerRunt 0x00000003 Configures the digitizer for runt triggering. Use the IviDigitizerRuntTrigger extension properties and methods to configure the trigger. 
    AgMD2TriggerGlitch 0x00000004 Configures the digitizer for glitch triggering. Use the IviDigitizerGlitchTrigger extension properties and methods to configure the trigger. 
    AgMD2TriggerTV 0x00000005 Configures the digitizer for triggering on TV signals. Use the IviDigitizerTVTrigger extension properties and methods to configure the trigger. 
    AgMD2TriggerWindow 0x00000006 Configures the digitizer for window triggering. Use the IviDigitizerWindowTrigger extension properties and methods to configure the trigger. 
    """
    Type  = p_(Int())
    
class IAgMD2TriggerSources(DeviceParameterContainerModel):  
    childFactory = Callable(IAgMD2TriggerSource)

class IAgMD2TriggerOutput(DeviceParameterModel):
    Enabled = p_(Bool())
    Offset  = p_(Float())
    Source  = p_(Unicode())
    

class IAgMD2Trigger(DeviceParameterModel):
    ActiveSource      = p_(Unicode())
    
    """ Delay
    Specifies the length of time from the trigger event to the first point in 
    the waveform record. If the value is positive, the first point in the waveform 
    record occurs after the trigger event. If the value is negative, the first point 
    in the waveform record occurs before the trigger event. The units are seconds.
    """
    Delay             = p_(Float()) 
    Output            = child_(Value(factory = IAgMD2TriggerOutput ))
    OutputEnabled     = p_(Bool())
    Sources           = child_(Value(factory = IAgMD2TriggerSources ))
    
class IIviDriverUtility(DeviceParameterModel):
    Disable           = p_(Value())
    ErrorQuery        = p_(Value())
    LockObject        = p_(Value())
    Reset             = p_(Value())
    ResetWithDefaults = p_(Value())
    ResetWithDefaults = p_(Value())
    SelfTest          = p_(Value())
    UnlockObject      = p_(Value())
    
class IAgMD2ModuleSynchronization(DeviceParameterModel):
    #: Not Supported
    pass
        
class IAgMD2Ex3(DeviceParameterModel):
    
    Acquisition           = child_( Value(factory = IAgMD2Acquisition           ))
    Calibration           = child_( Value(factory = IAgMD2Calibration           ))
    Channels              = child_( Value(factory = IAgMD2Channels              ))
    ControlIOs            = child_( Value(factory = IAgMD2ControlIOs            ))
    DriverOperation       = child_( Value(factory = IIviDriverOperation         ))
    Identity              = child_( Value(factory = IIviDriverIdentity          ))
    Initialized           = p_( Bool()                                       )
    InstrumentInfo        = child_( Value(factory = IAgMD2InstrumentInfo        ))
    LogicDevices          = child_( Value(factory = IAgMD2LogicDevices          ))
    ModuleSynchronization = child_( Value(factory = IAgMD2ModuleSynchronization ))
    ReferenceOscillator   = child_( Value(factory = IAgMD2ReferenceOscillator   ))
    SampleClock           = child_( Value(factory = IAgMD2SampleClock           ))
    Temperature           = child_( Value(factory = IAgMD2Temperature           ))
    Trigger               = child_( Value(factory = IAgMD2Trigger               ))
    Utility               = child_( Value(factory = IIviDriverUtility           ))
    
    
    
    def _get_root_lock(self):
        """ Get lock from IAgMD2Ex3 COM interface

        The Digitizer driver does not support the Utility.LockObject method:
            AgMD2: Does not support this class-compliant feature: method LockObject
            
        Instead, use a shared lock from the driver that manages the COM interface.
        
        """
        
        #: result = self.comif.Utility.LockObject()
        raise NotImplementedError

    def _release_root_lock(self):
        """ Release lock from IAgMD2Ex3 COM interface
        
        """
        
        #: result = self.comif.Utility.UnlockObject()
        
        raise NotImplementedError
    
if __name__ == '__main__':
    
    from pyspectro.apps import UHSFFTS_32k


    driver = UHSFFTS_32k('PXI4::4-0.0::INSTR')
    
    try:
        driver.connect()
        

        print(driver.model.to_string(recursive = True))
        
#         print topNode.Initialized
#         
#         topNode.update_parameters()
#         
#         print topNode.Initialized
# 
#         topNode.Initialized = False
#         
#         topNode.apply_parameters()
#         
#         print topNode.Initialized
        
    except Exception as e:
        raise
        
    finally:
        driver.disconnect()
            

    
    
    
    
    