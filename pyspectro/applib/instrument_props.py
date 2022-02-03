# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# -----------------------------------------------------------------------------

"""


"""

def get_temperature_properties(device):
    """ Get device temperatures

    Parameters
    -----------
    device : pyspectro.driver.Spectrometer

    Returns
    -------
    result : dict
        Dictionary of relevant device temperatures

    """
    result = {}

    #: Channel temperatures
    result['temp_ch1_c']         = device.instrument.Channels['Channel1'].Temperature
    result['temp_ch1_c_max']     = 100.0 #: from manual
    result['temp_ch2_c']         = device.instrument.Channels['Channel2'].Temperature
    result['temp_ch2_c_max']     = 100.0 #: from manual

    result['temp_adc_c']         = device.instrument.InstrumentInfo.MonitoringValues['MezzFrontEndA_AdcTemperature'].CurrentValue
    result['temp_adc_c_max']     = device.instrument.InstrumentInfo.MonitoringValues['MezzFrontEndA_AdcTemperature'].LimitHigh #: 125

    #: Board temperatures
    result['temp_board_c']       = device.instrument.Temperature.BoardTemperature
    result['temp_board_c_max']   = 85.0  #: from U5303a manual

    result['temp_dpu_c']         = device.instrument.InstrumentInfo.MonitoringValues['Dpu_Temperature'].CurrentValue
    result['temp_dpu_c_max']     = device.instrument.InstrumentInfo.MonitoringValues['Dpu_Temperature'].LimitHigh    #: 100 deg c


    return result

def get_slow_properties(device):
    """ Get slow propertyes

    Get properties that change slowly
    """

    result = {}

    result['Calibration_IsRequired']        = device.instrument.Calibration.IsRequired

    result['Ch1_FilterBypass']             = device.instrument.Channels['Channel1'].Filter.Bypass
    result['Ch1_FilterMaxFrequency']       = device.instrument.Channels['Channel1'].Filter.MaxFrequency
    result['Ch2_FilterBypass']             = device.instrument.Channels['Channel2'].Filter.Bypass
    result['Ch2_FilterMaxFrequency']       = device.instrument.Channels['Channel2'].Filter.MaxFrequency

    result['Ch1_Offset']                   = device.instrument.Channels['Channel1'].Offset
    result['Ch1_Range']                    = device.instrument.Channels['Channel1'].Range
    result['Ch2_Offset']                   = device.instrument.Channels['Channel2'].Offset
    result['Ch2_Range']                    = device.instrument.Channels['Channel2'].Range

    result['SampleRate']                   = device.sampleRate
    result['downsample_ratio']             = device.downsample_ratio
    result['Nfft']                         = device.Nfft

    return result



def get_instrument_properties(device):
    """ Get instrument data

    Retrieve static instrument data (i.e. data that does not change after
    a connection is made).  This only needs to be called once after connection.

    Parameters
    -----------
    device : pyspectro.driver.Spectrometer

    Returns
    -------
    result : dict
        Dictionary containing instrument data
    """

    result = {}

    result['Instrument_IOVersion']          = device.instrument.InstrumentInfo.IOVersion          #: 17.2.20407.1
    result['Instrument_SerialNumberString'] = device.instrument.InstrumentInfo.SerialNumberString #: MY00090383
    result['Instrument_Options']            = device.instrument.InstrumentInfo.Options            #: CH2,LX2,F10,DGT,FDK,INT,M02,SR1
    result['Instrument_NbrADCBits']         = device.instrument.InstrumentInfo.NbrADCBits         #: 12

    result['Instrument_Model']              = device.instrument.Identity.InstrumentModel #: U5303A
    result['Instrument_FirmwareRevision']   = device.instrument.Identity.InstrumentFirmwareRevision #: CTRL FPGA 1.0.352.54534, DPU FPGA 0.2.16.6M, FE CPLD 23/10
    result['Driver_Identifier']             = device.instrument.Identity.Identifier      #: AgMD2
    result['Driver_Revision']               = device.instrument.Identity.Revision        #: 1.8.444.4 (Fundamental 1.8.1470.4 svn #64330M)

    result['Driver_IoResourceDescriptor']   = device.instrument.DriverOperation.IoResourceDescriptor  #: PXI4::4-0.0::INSTR

    result['license_ok']                    = getattr(device, 'license_ok', None)

    device_id_hi = device.logicDevice['DpuA'].ReadRegisterInt32(0x341c)
    device_id_lo = device.logicDevice['DpuA'].ReadRegisterInt32(0x3418)
    device_id_hi &= 0xffffffff  #: Convert to unsigned int
    device_id_lo &= 0xffffffff  #: Convert to unsigned int
    result['device_id_1']                     = '{0:X}_{1:X}'.format(device_id_hi, device_id_lo)
    device_id_hi = device.logicDevice['DpuA'].ReadRegisterInt32(0x343c)
    device_id_lo = device.logicDevice['DpuA'].ReadRegisterInt32(0x3438)
    device_id_hi &= 0xffffffff  #: Convert to unsigned int
    device_id_lo &= 0xffffffff  #: Convert to unsigned int
    result['device_id_2']                     = '{0:X}_{1:X}'.format(device_id_hi, device_id_lo)

    return result

def get_instrument_properties_string(device):

    prop = get_instrument_properties(device)

    result = []
    result.append('{0}: {1}'.format('ResourceDescriptor' ,        prop['Driver_IoResourceDescriptor']))
    result.append('Instrument:')
    result.append('  {0}: {1}'.format('Platform' ,        prop['Instrument_Model']))
    result.append('  {0}: {1}'.format('Serial number' ,        prop['Instrument_SerialNumberString']))
    result.append('  {0}: {1}'.format('Options' ,        prop['Instrument_Options']))
    result.append('  {0}: {1}'.format('Firmware revision' ,        prop['Instrument_FirmwareRevision']))
    result.append('  {0}: {1}'.format('IO Version' ,        prop['Instrument_IOVersion']))
    result.append('Driver:')
    result.append('  {0}: {1}'.format('ID' ,        prop['Driver_Identifier']))
    result.append('  {0}: {1}'.format('Revision' ,        prop['Driver_Revision']))
    result.append('Device:')
    result.append('  1 {0}'.format(prop['device_id_1']))
    result.append('  2 {0}'.format(prop['device_id_2']))
    result.append('License OK: {0}'.format(prop['license_ok']))

    return '\n'.join(result)
