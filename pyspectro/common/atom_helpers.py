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



def prettyMembers(atomObject, indent = 1):
    """ Create a pretty string from the members of an Atom Object 
    
    result: str
        String containing the names and values of all members.
    """
    
    members = atomObject.members()
    
    maxNameLength = len( max( list(members), key=len) )
    
    formatStr = "{0:>%s} : {1}" % (maxNameLength + indent)
    
    result = []
    for name in members:
        val = getattr(atomObject, name)
        result.append(format(formatStr.format(name, str(val))))
        
    return '\n'.join(result)


if __name__ == '__main__':
    
    from atom.api import Atom, Int, Typed
    
    class Atom_1(Atom):
        a = Int(1)
        b = Int(2)

    class Atom_2(Atom):
        c = Int(3)
        d = Int(4)
        e = Typed(Atom_1,())
        
    obj = Atom_2()
    print(prettyMembers(obj))
        
        
