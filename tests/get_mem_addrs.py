#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------
""" Get memory addresses

This script computes the mapping of FFT bins to memory addresses
and saves the results to files (one each for DDRA/B).

"""

import numpy as np

#: Create a memory converter object to pre-compute index map
from pyspectro.drivers.Spectrometer import MemoryConverter

mc = MemoryConverter(32768, False)
np.savetxt("memidx_n32k_real_ddra.txt", mc._ddra_indices, fmt = '%i', delimiter=",") 
np.savetxt("memidx_n32k_real_ddrb.txt", mc._ddrb_indices, fmt = '%i',delimiter=",") 

mc = MemoryConverter(16384, True)
np.savetxt("memidx_n16k_complex_ddra.txt", mc._ddra_indices, fmt = '%i', delimiter=",") 
np.savetxt("memidx_n16k_complex_ddrb.txt", mc._ddrb_indices, fmt = '%i',delimiter=",") 

mc = MemoryConverter(8192, True)
np.savetxt("memidx_n8k_complex_ddra.txt", mc._ddra_indices, fmt = '%i', delimiter=",") 
np.savetxt("memidx_n8k_complex_ddrb.txt", mc._ddrb_indices, fmt = '%i',delimiter=",") 

mc = MemoryConverter(4096, True)
np.savetxt("memidx_n4k_complex_ddra.txt", mc._ddra_indices, fmt = '%i', delimiter=",") 
np.savetxt("memidx_n4k_complex_ddrb.txt", mc._ddrb_indices, fmt = '%i',delimiter=",") 

