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

__author__    = 'Mike Babst'
__title__     = 'pyspectro'
__license__   = 'Licensed with restricted rights.  See LICENSE.txt for details'
__copyright__ = 'Copyright (c) 2016, DSPlogic, Inc.  All Rights Reserved'

from _version import __version__

import sys
if sys.version_info[:2] < (2, 7):
    m = "Python version 2.7 or later is required for {0} (%d.%d detected).".format(__title__)
    raise ImportError(m % sys.version_info[:2])
del sys



