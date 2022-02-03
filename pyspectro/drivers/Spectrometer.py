# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# -----------------------------------------------------------------------------

#: Package imports
from atom.api import Atom, Int, Bool, Property, Float, Typed, Tuple, Str, List
import numpy as np
from .dsplogic import BUFFER_ID
from ..common.bitreversal import bitrevorder
from ..common.bitmanipulation import testBit, setBit, clearBit
from .AgMD2Digitizer import Digitizer
from .license import read_license_keys

import logging
logger = logging.getLogger(__name__)

""" Driver register map

"""
REGISTER_MAP = {
    'main_control' : 0x3300,
    'main_status'  : 0x3304,
    'num_average'  : 0x3308,
    'msrmnt_cnt'   : 0x330C,
    'overflow'     : 0x3310,
    '_tg_control1' : 0x3314,
    '_tg_control2' : 0x3318,
    '_reserved1'   : 0x331C,
    '_tg_ph0'      : 0x3320,
    '_tg_ph1'      : 0x3324,
    '_tg_ph2'      : 0x3328,
    '_tg_ph3'      : 0x332C,
    '_tg_ph4'      : 0x3330,
    '_tg_ph5'      : 0x3334,
    '_tg_ph6'      : 0x3338,
    '_tg_ph7'      : 0x333c,
    'interleave'   : 0x3340,
    'downsample'   : 0x3344,
    'lic_stat'     : 0x3400,
    'lic_key_0'    : 0x3404,
    'lic_key_1'    : 0x3408,
    'lic_key_2'    : 0x340C,
    'lic_key_3'    : 0x3410
}


class SpectrometerApplication(Atom):
    """ Spectrometer application

    This object specifies a custom FFT spectrometer application
    """

    Nfft = Int()

    complexData = Bool()

    interleaving = Bool()

    required_hwcfg = Tuple(item=Str())

    bitfile = Str()

    floating_point = Bool()

    downsample_ratio = List(item=int)


class Spectrometer(Digitizer):
    """ Spectrometer driver

    This class implementes python driver for the DSPlogic's
    1 GHz Wideband FFT Spectrometer with 16k channels.
    It may be used directly or referred to as a model
    for drivers written in other languages.

    It should be instantiated using the helper function
    UHSFFTS_32k()

    Properties
    ----------

    numAverages : int
        Number of averages to accumulate.
        The input can range from 2 to 1,000,000 (approximately 16 seconds)

    continuousMode: bool
        When false, the spectrometer is in one-shot mode.  It will perform the
        requested number of accumulations and return the result.
        When true, the spectrometer is in continuous mode.  It will continue
        writing measurement to memory at the end of each accumulation period.

    measurementCount : int
        The number of measurements that have been performed since the
        start of acquisition. In one-shot mode, measurementCount will be
        incremented to 1 after numAverages accumulations have been
        performed and the resulting measurement has been written to memory.
        In continuous mode, the measurementCount will continue to increment
        until a stopAcquisiton command is received.

    measurementComplete : bool
        During one-shot acquisition, this property indicates that the measurement
        has been completed and the result is ready in DDR memory

    overflow : int
        A non-zero value indicates that a signal overflow error occurred internal
        to the DSP core.

    memoryError: int
        A non-zero value indicates that a DDR memory conflict has occurred between
        the software and the DSP core.

    """

    #: FFT Length (read-only)
    Nfft = property(lambda self: self.app.Nfft)

    #: Effective sample rate (read-only)
    #: Includes effect of interleaving and downsampling
    sampleRate = property(lambda self: self._get_sample_rate())

    #: Number of averages (R/W)
    numAverages = Property()

    #: Set continuous mode vs. one-shot (R/W)
    continuousMode = Property()

    #: Set continuous mode vs. one-shot (R/W)
    disablePolyphase = Property()

    #: Downsample Ratio
    #: Read (all platforms), Write (supported platforms).
    downsample_ratio = Property()

    #: Current measurement count (Read-Only)
    measurementCount = property(lambda self: self.read_register('msrmnt_cnt'))

    #: Current measurement count (Read-Only)
    overflow = property(lambda self: self.read_register('overflow'))

    #: Check License Status (Read-Only)
    license_ok = property(lambda self: (testBit( self.read_register('lic_stat'), 1) > 0) )

    #: An memory error
    memoryError = Property()

    #: Application
    app = Typed(SpectrometerApplication,())


    #: PRIVATE PROPERTIES
    #:-------------------

    #: Test mode for internal use
    _testMode   = Property()
    __testMode = Bool()

    #: Test frequency
    _testFreq  = Property()
    __testFreq = Float()

    def __init__(self, resourceName, app, **kwargs):
        """ Initialize spectrometer driver

        Delegate initialization to superclass (Digitizer)
        and turn on required interleaving
        """

        super(Spectrometer, self).__init__(resourceName=resourceName, app=app, **kwargs)

        #: Set bitfile from application
        self.bitfile = self.app.bitfile


    def read_register(self, reg):
        """ Read control register

        Parameters
        ----------
        reg : str
            Name of register in REGISTER_MAP

        """

        if reg in REGISTER_MAP:
            reg_addr = REGISTER_MAP[reg]
            reg = self.logicDevice['DpuA'].ReadRegisterInt32(reg_addr)
            return reg
        else:
            raise Exception('Invalid register %s' % reg)

    def write_register(self, reg, val):
        """ Write control register

        Parameters
        ----------
        reg : str
            Name of register in REGISTER_MAP
        val : Int32
            32-bit register value

        """
        if reg in REGISTER_MAP:
            reg_addr = REGISTER_MAP[reg]
            self.logicDevice['DpuA'].WriteRegisterInt32(reg_addr, val)

        else:
            raise Exception('Invalid register %s' % reg)


    def connect(self):

        #: Call superclass (AgMD2Device) connection function
        connected = super(Spectrometer, self).connect()

        if connected:

            #: Verify that application is supported

            if self.app_supported():
                logger.info('Application ready')

                #: Set HW interleaving as required by application
                if self.app.complexData:

                    self.app.interleaving = False

                else:

                    if self.app.interleaving:
                        self.interleaving = True
                    else:
                        self.interleaving = False

                #: Reapply setup w/ application config
                self.instrument.Acquisition.ApplySetup()

            else:
                logger.error('Application not supported')

            #: Get license and apply to instrument
            if not self._get_license():
                logger.error('Hardware license failed')


        return connected

    def app_supported(self):
        """ Check hardware support for application

        """
        if self.isConnected:

            app_ok = True

            for req in self.app.required_hwcfg:

                if req not in self.options:
                    logger.error('Required hardware configuration not available: {}'.format(req))
                    app_ok = False

            return app_ok

        else:

            return None


    def _get_license(self):
        """ Read license from file and write to instrument

        """
        lic_ok = False

        #: Read device serial number
        serial_no = self.instrument.InstrumentInfo.SerialNumberString

        #: Read license file
        logger.info('Getting license for instrument: %s' % serial_no)
        keys, err, licfile = read_license_keys(serial_no)

        if err:
            logger.error(err)
            return
        else:
            logger.info('License file OK: %s' % licfile)

        #: Apply license
        self.write_register('lic_key_0', int(keys['key0'], 16) )
        self.write_register('lic_key_1', int(keys['key1'], 16) )
        self.write_register('lic_key_2', int(keys['key2'], 16) )
        self.write_register('lic_key_3', int(keys['key3'], 16) )

        result = self.read_register('lic_stat')
        if result == 3:
            logger.info('License OK for instrument %s' % serial_no)
            lic_ok = True
        elif result == 1:
            logger.error('Invalid license key for instrument %s' % serial_no)
        else:
            logger.error('Incompatible bitfile %s.  Please update bitfile' % self.bitfile)

        return lic_ok

    def _get_sample_rate(self):
        """ Return the effective sample rate, after factoring in
        platform interleaving and downsampling

        """

        hw_sampleRate = self.instrument.Acquisition.SampleRate

        return hw_sampleRate / float(self.downsample_ratio)



    def read_memory(self, chan):
        """ Read (partial) measurement from digitizer memory

        This function reads measurement data from DDR memory.
        The data is split between channel 1 and channel 2.

        The MemoryConverter class can be used to map the DDR memory contents
        returned by this method into FFT bins in normal order

        Parameters
        ----------
        chan : int
            Set to 1 to read channel 1 memory (from DDR A)
            Set to 2 to read channel 2 memory (from DDR B)

        Returns
        -------
        result : np.array(dtype=float32)
            Processing results contained in single channel of DDR memory
            Length of result is
                Nfft/2 for FFT of complex data and
                Nfft/4 for FFT of real data

        """

        if self.app.complexData:
            nbrint32 = self.app.Nfft//2
        else:
            nbrint32 = self.app.Nfft//2//2


        if chan == 1:

            self.memoryBank['DpuA']['DDR3A'].AccessMode = 1 # DDRA in read mode
            buff = BUFFER_ID['DpuA.DDR3A']
            data_int32 = self.logicDevice['DpuA'].ReadIndirectInt32(buff, 0x0, nbrint32)
            self.memoryBank['DpuA']['DDR3A'].AccessMode = 0

        elif chan == 2:

            self.memoryBank['DpuA']['DDR3B'].AccessMode = 1 # DDRA in read mode
            buff = BUFFER_ID['DpuA.DDR3B']
            data_int32 = self.logicDevice['DpuA'].ReadIndirectInt32(buff, 0x0, nbrint32)
            self.memoryBank['DpuA']['DDR3B'].AccessMode = 0

        else:

            raise Exception('Invalid Channel ID')

        FirstValidPoint = data_int32[2]
        ActualPoints    = data_int32[1]

        result      = np.array(data_int32[0][FirstValidPoint : FirstValidPoint + ActualPoints ],
                               dtype = np.uint32)

        if self.app.floating_point:
            result = result.view('float32')

        return result

    """ Property getters and setters
    """
    def _get_numAverages(self):

        return self.read_register('num_average') + 1

    def _set_numAverages(self, val):

        self.write_register('num_average', val-1)

    def _get_continuousMode(self):

        mcreg = self.read_register('main_control')

        return testBit(mcreg, 0)

    def _set_continuousMode(self, val):

        mcreg = self.read_register('main_control')

        if val:
            mcreg = setBit(mcreg, 0)
        else:
            mcreg = clearBit(mcreg, 0)

        self.write_register('main_control', mcreg)

    def _get_disablePolyphase(self):

        mcreg = self.read_register('main_control')

        return testBit(mcreg, 1)

    def _set_disablePolyphase(self, val):

        mcreg = self.read_register('main_control')

        if val:
            mcreg = setBit(mcreg, 1)
        else:
            mcreg = clearBit(mcreg, 1)

        self.write_register('main_control', mcreg)

    def _get_downsample_ratio(self):
        """ Return downsample ratio  """

        mcreg = self.read_register('downsample')

        if testBit(mcreg, 0):

            return 2

        else:

            return 1

    def _set_downsample_ratio(self, val):

        if val == 1:

            reg = 0

        elif val == 2:

            reg = 1

        else:
            raise Exception('Invalid downsample ratio {}.  Must be 1 or 2.'.format(val))

        self.write_register('downsample', reg)


    def _get__testMode(self):

        mcreg = self.read_register('_tg_control1')

        return testBit(mcreg, 0)

    def _set__testMode(self, val):

        mcreg = self.read_register('_tg_control1')

        if val:
            mcreg = setBit(mcreg, 0)
            self.__testMode = True
        else:
            mcreg = clearBit(mcreg, 0)
            self.__testMode = False

        self.write_register('_tg_control1', mcreg)

    def _get__testFreq(self):

        return self.__testFreq

    def _set__testFreq(self, f):

        Fs = self.sampleRate

        if f > Fs/2.0:
            raise Exception('{} is larger than maximum frequency {}'.format(f, Fs/2.0))

        if self.app.complexData:
            if f < -Fs/2.0:
                raise Exception('{} is less than minimum frequency {}'.format(f, -Fs/2.0))
        else:
            if f < 0:
                raise Exception('Frequency must be positive')



        phst = int( float(f)/ Fs * (2**28))

        self.write_register('_tg_ph0',      0 * phst)
        self.write_register('_tg_ph1',      1 * phst)
        self.write_register('_tg_ph2',      2 * phst)
        self.write_register('_tg_ph3',      3 * phst)
        self.write_register('_tg_ph4',      4 * phst)
        self.write_register('_tg_ph5',      5 * phst)
        self.write_register('_tg_ph6',      6 * phst)
        self.write_register('_tg_ph7',      7 * phst)
        self.write_register('_tg_control2', 8 * phst)

        self.__testFreq = float(phst) / (2**28) * 2e9

        if self.__testMode:
            mcreg = self.read_register('_tg_control1')
            mcreg = clearBit(mcreg, 0)
            mcreg = setBit(mcreg, 0)


    def _get_memoryError(self):
        reg = self.read_register('main_status')
        return reg & 0x000000ff


    """ Addtional status

    """
    def _fpgaCanAccessMemory(self):
        reg = self.read_register('main_status')
        if reg & 0x01000000:
            return True
        else:
            return False

    def _fpgaCoreIsActive(self):
        #: As determined by mem_active
        reg = self.read_register('main_status')
        if reg & 0x04000000:
            return True
        else:
            return False

    def debug_accum_state(self):
        reg = self.read_register('main_status')
        mask = 0x0000ff00
        return (reg & mask) >> 8

    def debug_mem_state(self):
        reg = self.read_register('main_status')
        mask = 0x00ff0000
        return (reg & mask) >> 16


class MemoryConverter(Atom):
    """ Convert DDR memory to FFT format

    A processor that converts data from instrument memory format
    into normal FFT format.

    The indices that map memory locations to FFT bins are pre-computed at initialization
    to improve performance.

    Use the process() method to perform the conversion
    """

    Nfft = Int()
    complexData = Bool()

    #: Private storage
    _ddra_indices   = Typed(np.ndarray)
    _ddrb_indices   = Typed(np.ndarray)

    def __init__(self, Nfft, complexData):
        """ Initialize the memory converter by computing the FFT indices of
        results stored in both DDR channels.

        Parameters
        ----------

        Nfft : int
            FFT Length

        complexData : int
            True: FFT of complex data (interleaving off)
            False: FFT of real data (interleaving on)

        """
        self.Nfft = Nfft
        self.complexData = complexData

        nfftdiv2 = Nfft//2

        if complexData:

            #: Pre-compute bit reversal indices
            bitrev_indices =  bitrevorder(np.array(range(Nfft)))

            #: Precompute FFT channel index for each location in memory
            #: FOR NOW, JUST USE LINEAR INDEX
            self._ddra_indices = np.arange(nfftdiv2, dtype = int)
            self._ddrb_indices = np.arange(nfftdiv2, dtype = int)+ Nfft//2

            #: data to ddr is 16 wide
            for k in range(Nfft// 16 ):

                # Get top half
                self._ddra_indices[k*8+0] = bitrev_indices[k*16+0]
                self._ddra_indices[k*8+1] = bitrev_indices[k*16+1]
                self._ddra_indices[k*8+2] = bitrev_indices[k*16+2]
                self._ddra_indices[k*8+3] = bitrev_indices[k*16+3]
                self._ddra_indices[k*8+4] = bitrev_indices[k*16+4]
                self._ddra_indices[k*8+5] = bitrev_indices[k*16+5]
                self._ddra_indices[k*8+6] = bitrev_indices[k*16+6]
                self._ddra_indices[k*8+7] = bitrev_indices[k*16+7]

                # Get bottom half
                self._ddrb_indices[k*8+0] = bitrev_indices[k*16+8]
                self._ddrb_indices[k*8+1] = bitrev_indices[k*16+9]
                self._ddrb_indices[k*8+2] = bitrev_indices[k*16+10]
                self._ddrb_indices[k*8+3] = bitrev_indices[k*16+11]
                self._ddrb_indices[k*8+4] = bitrev_indices[k*16+12]
                self._ddrb_indices[k*8+5] = bitrev_indices[k*16+13]
                self._ddrb_indices[k*8+6] = bitrev_indices[k*16+14]
                self._ddrb_indices[k*8+7] = bitrev_indices[k*16+15]


            # Perform FFTSHIFT operation (swap upper and lower halves) so negative
            # frequencies are on the left.
            tvec = np.copy(self._ddra_indices)
            for k in range(nfftdiv2):
                if tvec[k] < nfftdiv2:
                    self._ddra_indices[k] += nfftdiv2
                else:
                    self._ddra_indices[k] -= nfftdiv2

            tvec = np.copy(self._ddrb_indices)
            for k in range(nfftdiv2):
                if tvec[k] < nfftdiv2:
                    self._ddrb_indices[k] += nfftdiv2
                else:
                    self._ddrb_indices[k] -= nfftdiv2



        else:

            #: Pre-compute bit reversal indices
            bitrev_indices =  bitrevorder(np.array(range(Nfft//2)))

            #: Precompute FFT channel index for each location in memory
            self._ddra_indices = np.zeros(Nfft//2//2, dtype = int)
            self._ddrb_indices = np.zeros(Nfft//2//2, dtype = int)

            for k in range(Nfft//2//2//8):
                self._ddra_indices[k*8 : (k+1)*8] = bitrev_indices[ 2*k   *8 + np.arange(8)]
                self._ddrb_indices[k*8 : (k+1)*8] = bitrev_indices[(2*k+1)*8 + np.arange(8)]

    def process(self, data_ddra, data_ddrb):
        """ Convert memory data to FFT format

        Parameters
        ----------
        data_ddra, data_ddrb : numpy.array dtype='flat32'
            Contents read from DDR A and DDR B memory.
            Length of each input:
                Nfft/2 (fft of complex data)
                Nfft/4 (fft of real data)


        """
        if self.complexData:
            result = np.empty( (self.Nfft,), dtype=np.float64 )

        else:
            result = np.empty( (self.Nfft//2,), dtype=np.float64 )

        #: Assign memory data to FFT bins
        result[self._ddra_indices] = data_ddra
        result[self._ddrb_indices] = data_ddrb

        return result


if __name__ == "__main__":

    pass
