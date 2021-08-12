# ------------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
# ------------------------------------------------------------------------------
from __future__ import (division, print_function, absolute_import)


""" Buffer IDs

This 64 GB address space is accessible from the host computer over PCIe through an address indirection mechanism: 

Each memory is assigned a Buffer ID. 
    By setting the Buffer ID in the PCIe interface a window with AXI4-Full base address and high address corresponding 
    to the selected memory area is opened, then memory can be accessed through Programmed I/O or DMA.
    
    Buffer IDs 0..15 are reserved for the Digitizer region. 
    Buffer IDs 16..31 are available for the FDK User

The user core FPGA code defines the following
"""
BUFFER_ID  = {'DpuA.QDR2' : 20,
              'DpuA.DDR3A': 28,
              'DpuA.DDR3B': 30
               }

