# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# -----------------------------------------------------------------------------

try:
    from _version_build import _buildid
except:
    _buildid = "0"

_major = 1
_minor = 5

__version__ = "%s.%s.%s" % (_major, _minor, _buildid)
