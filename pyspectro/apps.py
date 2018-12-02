#------------------------------------------------------------------------------
# Copyright (c) 2016-2018, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------

from pyspectro.drivers.Spectrometer import Spectrometer, SpectrometerApplication


def get_application(Nfft):
    """ Get user application
    This function returns a SpectrometerApplication based upon a user-requested
    FFT length.  
    
    """
    if Nfft == 32768:
        
        #bitfile = 'U5303ADPULX2FDK_uhsffts_32k_float_1_0_229.bit'
        app = SpectrometerApplication(
                    Nfft = 32768,
                    complexData = False,
                    interleaving = True,                      
                    floating_point = True,
                    bitfile = 'U5303ADPULX2FDK_uhsffts_32k_float_1_1_231.bit',
                    required_hwcfg = ('CH2','LX2','F10','DGT','FDK','INT','M02','SR1') )    

        return app
    
    else:
    
        return None
    


""" Top level spectrometer classes for user instantiation

"""
def UHSFFTS_32k(resourceName=''):
    
    app = get_application(Nfft=32768)
    
    return Spectrometer(resourceName, app=app)

def UHSFFTS_4k_complex(resourceName=''):
    
    #bitfile = 'U5303ADPULX2FDK_uhsffts_32k_float_1_0_229.bit'
    app = SpectrometerApplication(
                Nfft = 4096,
                complexData = True,   
                interleaving = False,                   
                floating_point = True,
                bitfile = 'U5303ADPULX2FDK_uhsffts_32k_float_1_1_231.bit',
                required_hwcfg = ('CH2','LX2','F10','DGT','FDK','INT','M02','SR1') )    
    
    return Spectrometer(resourceName, app=app)

