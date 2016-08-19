
import numpy as np

#: Create a memory converter object to pre-compute index map
from pyspectro.drivers.Spectrometer import MemoryConverter
mc = MemoryConverter(32768)

#: Save to file
np.savetxt("idx_ddra.csv", mc._ddra_indices, delimiter=",") 
np.savetxt("idx_ddrb.csv", mc._ddra_indices, delimiter=",") 
