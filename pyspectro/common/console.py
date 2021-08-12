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


from atom.api import Atom, Unicode
import sys

class ConsoleTextWriter(Atom):

    text = Unicode()
    
    def write(self, newtext):
        
        self.text = ''.join([newtext, self.text])
        
    def enable(self):
        sys.stdout = self
        
    def disable(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__        

    def __del__(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__        



if __name__ == '__main__':
    
    obj = ConsoleTextWriter()
    
    print('hello 1')
    
    obj.enable()
    
    print('hello 2')
    
    obj.disable()
    
    print('hello 3')
    
    print(obj.text)