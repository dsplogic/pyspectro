#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------

import os
from enaml.icon import Icon, IconImage
from enaml.image import Image


def loadIconImage(name, mode='normal', state='off'):
    
    dirname = os.path.dirname(__file__)
    
    fname = os.path.join(dirname, 'icons', '%s.png' % name)
    
    with open(fname, 'rb') as f:
        data = f.read()
        
    img = Image(data=data)
    
    icg = IconImage(image=img, mode=mode, state=state)
    
    return icg


def dsplogicIcon():
    dsplogic = loadIconImage('dsplogic-diamond-512')
    
    return Icon(images=[dsplogic])
    
def connectedIcon():
    led_green = loadIconImage('led_green',
                              mode = 'normal')
    
    led_red = loadIconImage('led_red',
                              mode = 'disabled')
    
    return Icon(images=[led_green, led_red])
