# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
# -----------------------------------------------------------------------------



def testBit(int_type, offset):
    mask = 1 << offset
    return(int_type & mask)

def setBit(int_type, offset):
    mask = 1 << offset
    return(int_type | mask)

def clearBit(int_type, offset):
    mask = ~(1 << offset)
    return(int_type & mask)

def toggleBit(int_type, offset):
    mask = 1 << offset
    return(int_type ^ mask)
