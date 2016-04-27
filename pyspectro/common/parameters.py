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



from atom.api import Atom, Typed, Value, Int, Bool, Enum, Property, Event

from enaml.core.object import Object, flag_generator, flag_property

#: The flag indicating that the DeviceParameterModel object has been initialized.
INITIALIZED_FLAG = flag_generator.next()

def _isParameter(member):
    if member.metadata:
        if 'p_member' in member.metadata:
            return True
    return False

def _isChild(member):
    if member.metadata:
        if 'c_member' in member.metadata:
            return True
    return False


class Hobject(Object):
    #: An event fired when an object is initialized. It is triggered
    #: once during the object lifetime, at the end of the initialize
    #: method.
    initialized = Event()

    #: A property which gets and sets the initialized flag. This should
    #: not be manipulated directly by user code.
    is_initialized = flag_property(INITIALIZED_FLAG)
    
    def initialize(self):
        """ Initialize this object all of its children recursively.

        This is called to give the objects in the tree the opportunity
        to initialize additional state which depends upon the object
        tree being fully built. It is the responsibility of external
        code to call this method at the appropriate time. This will
        emit the `initialized` signal after all of the children have
        been initialized.

        """
        # Iterate over a copy since the children add and remove
        # other children during initialization.
        for child in self.children[:]:
            if isinstance(child, Hobject):
                child.initialize()
        self.is_initialized = True
        self.initialized()

    def destroy(self):
        """ An overridden destructor method for Hobject cleanup.

        """
        self.is_initialized = False
        super(Hobject, self).destroy()
        
        
def p_(member, writable= False):
    """ Mark an Atom member as a Parameter

    Parameters
    ----------
    member : Member
        The atom member to mark as a parameter

    writable : bool, optional
        Whether the member can be written to the device interface.
        The default is False.

    """
    metadata = member.metadata
    if metadata is None:
        metadata = member.metadata = {}
    metadata['p_member'] = True
    metadata['p_writable'] = writable
    return member

def child_(member):
    """ Mark an Atom member as a pointer to a Child Hobject
 
    Parameters
    ----------
    member : Member
        The atom member to mark as a child Hobject
 
    """
    metadata = member.metadata
    if metadata is None:
        metadata = member.metadata = {}
    metadata['c_member'] = True
    return member
 
 
def m_(member):
    """ Mark an Atom member as a Method
 
    Parameters
    ----------
    member : Member
        The atom member to mark as a method
 
    writable : bool, optional
        Whether the member can be written to the device interface.
        The default is False.
 
    """
    metadata = member.metadata
    if metadata is None:
        metadata = member.metadata = {}
    metadata['m_member'] = True
    return member

import atom

class ParameterModel(Hobject):
    """ Sentinel class for Attribute Models
    
    This class is used to model the attributes of a hierarchical object.
    
    Model parameters are specified by marking the Atom Members 
    of a ParameterModel subclass using the 'p_' function.
    
    Child objects are specified by marking the Atom Members  
    of a ParameterModel subclass using the 'child_' function.
    """

    fullname = Property()

    def __init__(self, parent=None, **kwargs):
        """ Initialize a ParameterModel.
     
        Parameters
        ----------
        parent : Object or None, optional
            The Object instance which is the parent of this object, or
            None if the object has no parent. Defaults to None.
     
        **kwargs
            Additional keyword arguments to apply as attributes to the
            object.
        """
        super(ParameterModel, self).__init__(parent, **kwargs)
        
        #: Search for and take ownership of any child ParameterModel objects
        #for name, member in self.members().iteritems():
        for name, member in self.members().iteritems():
            
            #if type(member) is atom.scalars.Value:
            if _isChild(member):
                model = getattr(self, name, None)
                if isinstance(model, ParameterModel):
                    #print('%s Claiming child %s' % (self.__class__, name) )
                    model.set_parent(self)
                    model.name = name
                else:
                    raise Exception('Child must be a ParameterModel object')
        #print('%s constructor finished' % self.__class__)
                
    def __del__(self):
        pass
        #print 'deleted %s:%s' % (self.__class__, self.name)
            
    def _iter_param_members(self, writable= None):
        
        members = self.members()
        for name, member in members.iteritems():
            if _isParameter(member):
                
                if writable is not None:
                    if member.metadata['p_writable'] <> writable:
                        continue
                
                yield name, member
        
    def iter_params(self, writable= None):
        
        for name, _ in self._iter_param_members(writable= writable):
            
            yield name, getattr(self, name)
                
    def iter_names(self, writable= None):
        
        for name, _ in self._iter_param_members(writable= writable):
            
            yield name

    def iter_values(self, writable= None):
    
        for name, _ in self._iter_param_members(writable= writable):
            yield name, getattr(self, name)

    def _get_fullname(self):
        names = [self.name]
        for parent in self.traverse_ancestors():
            names.append(parent.name)
        
        return '.'.join(reversed(names))

    def to_string(self, recursive = False):
        """ Create a pretty string from the Parameters in a ParameterModel 
        
        result: str
            String containing the names and values of all members.
        """
        result = []

        #result.append("{0} ({1}):".format(self.fullname, type(self)))
        result.append("{0}:".format(self.fullname))
                
        indent = 2;
        
        names = list(self.iter_names())
        if len(names) > 0:
            maxNameLength = len( max(names, key=len) )
        else:
            maxNameLength = 0;
            
        maxNameLength = max(maxNameLength, 20)
        
        formatStr = "{0:>%s} : {1}" % (maxNameLength + indent) #: Centered
        formatStr = "  {0} : {1}"
    
        
        for name, val in self.iter_params():
        
            result.append(format(formatStr.format(name, str(val))))

        for child in self.children:
            
            result.append(child.to_string(recursive = recursive))
                
        return '\n'.join(result)
        
        
        
if __name__ == '__main__':

    class TestModel(ParameterModel):
        IntParam1 = p_(Int())
        IntParam2 = p_(Int(), writable = True)
        IntParam3 = p_(Int())
        IntParam4 = p_(Int(), writable = False)
        IntParam5 = p_(Int(), writable = True)
        
        othermember = Bool()

    class TestTop(ParameterModel):
        
        topParam = p_(Int())
        
        child1   = Value(factory = TestModel)
                
    
    pm = TestModel(name='aaa')

    print('all')
    for name, val in pm.iter_params():
        print(':'.join([name, str(val)]))
    
    print('writable')
    for name, val in pm.iter_params(writable = True):
        print(':'.join([name, str(val)]))
    
    print('nonwritable')
    for name, val in pm.iter_params(writable = False):
        print(':'.join([name, str(val)]))
    
    print('testTop')
    top = TestTop(parent=None, name='top')
    for name, val in top.iter_params():
        print(':'.join([name, str(val)]))
        
    
    for child in top.children:
        print(child.fullname)
        
    top.destroy()
        

