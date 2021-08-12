#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
#------------------------------------------------------------------------------

from pyspectro.apps import UHSFFTS_32k
from pyspectro.applib.instrument_props import get_instrument_properties_string

ffts = UHSFFTS_32k('PXI4::4-0.0::INSTR')
ffts.connect()
result = get_instrument_properties_string(ffts)
print result
ffts.disconnect()

