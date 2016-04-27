#------------------------------------------------------------------------------
# Copyright (c) 2016, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#
# Function bitrevorder_gen licensed according to source: 
#   http://ryancompton.net/2014/06/05/bit-reversal-permutation-in-python/
#
#------------------------------------------------------------------------------
from __future__ import (division, print_function, absolute_import)


""" Bit reversal utilities

"""

import numpy as np

def bitrev_map(nbits):

    assert isinstance(nbits, int) and nbits > 0, 'bit size must be positive integer'
    dtype = np.uint32 if nbits > 16 else np.uint16
    brmap = np.empty(2**nbits, dtype=dtype)
    int_, ifmt, fmtstr = int, int.__format__, ("0%db" % nbits)
    for i in range(2**nbits):
        brmap[i] = int_(ifmt(i, fmtstr)[::-1], base=2)
    return brmap

def bitrevorder_gen(a):
    """ 
    Source: Ryan Compton
            http://ryancompton.net/2014/06/05/bit-reversal-permutation-in-python/
    """
    
    n = a.shape[0]
    
    assert(not n & (n-1) ) # assert that n is a power of 2

    if n == 1:
        yield a[0]
        
    else:
        
        even_index = np.arange(n//2)*2
        
        odd_index = np.arange(n//2)*2 + 1
        
        for even in bitrevorder_gen(a[even_index]):
            
            yield even
            
        for odd in bitrevorder_gen(a[odd_index]):
            
            yield odd
            
def bitrevorder(a):
    
    N = a.shape[0]      
    
    x = np.zeros(N, dtype= a.dtype )
    
    for i, el in enumerate(bitrevorder_gen(a) ): 
        
        x[i] = el
    
    return x

