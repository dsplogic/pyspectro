#------------------------------------------------------------------------------
# Copyright (c) 2016-2019, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------

from atom.api import Typed
from atom.api import Atom, Value, Unicode, Tuple, Int, Dict, Callable

from pyspectro.common.parameters import ParameterModel, p_

#: Keep comtypes logging quiet
import logging
logging.getLogger("comtypes").setLevel(logging.WARNING)

import comtypes

#: Try to import AgMD2Lib.
#: If it does not exist, create object to generate 
#: interface code
try:
    from comtypes.gen import AgMD2Lib
except:
    try: # The following may fail if a device driver is not installed.
        import comtypes.client
        comtypes.client.CreateObject("AgMD2.AgMD2")
        from comtypes.gen import AgMD2Lib
    except:
        pass

logger = logging.getLogger(__name__)


class DeviceParameterModel(ParameterModel):
    """ A ParameterModel that is connected to a physical device through a 
    communication interface.

    It can be attached to a ComInterface object and used to 
    update the model attributes form the COM oject or apply 
    the model attributes to the COM object    

    """

    """ Communication interface
    
    The communication interface must have Python attributes equivalent to 
    those maked in the ParameterModel, such that the python getattr() and 
    setattr() methods will read and write the ParameterModel values to/from the
    phtsical device attached to the interface.
    
    """    
    comif = Typed(comtypes.IUnknown)
    
    def get_lock(self):
        """ Get mulithreaded lock
        
        Get a multi-threaded lock object from the root DeviceParameterModel.
        """
        root = self.root_object()
        if self is root:
            self._get_root_lock()
        else:
            root.get_lock()

    def release_lock(self):
        """ Release multithreaded lock
        
        """
        root = self.root_object()
        if self is root:
            self._release_root_lock()
        else:
            root.release_lock()

    def _get_root_lock(self):
        """ Get multi-threaded lock from device driver.
        
        This method must be overridden by the root object to acquire the lock from
        the communication device driver.
        """
        raise NotImplemented

    def _release_root_lock(self):
        """ Release multi-threaded lock from device driver.
        
        This method must be overridden by the root object to release the lock from
        the communication device driver.
        """
        raise NotImplemented

    def initialize(self, comif= None):
        """ A reimplemented initializer.

        This initializer will assign the comif interface to all child objects.

        Parameters:
        comif: comtypes.IUnknown (optional)
            The COM interface to attach to the model.  It not supplied, the interface is
            automatically created based upon the Parameter name
            
        """
        if not(self.parent):
            #: This is the top level Model
            if comif:
                self.comif = comif
            else:
                if not self.comif:
                    raise Exception('Cannot initialize model.  Top level object has no COM interface')
        else:
            #: Get COM interface 
            if comif:
                self.comif = comif
            else:
                try:
                    self.comif = getattr(self.parent.comif, self.name)
                except Exception as e:
                    raise Exception("Error getting COM parameter '%s' from parent interface %s.\n %s" % (self.name, self.parent.comif, str(e)))
            
            
        super(DeviceParameterModel, self).initialize()

        #: Initial update of parameters
        self.update_parameters()


    def destroy(self):
        """ A reimplemented destructor.

        """
        super(DeviceParameterModel, self).destroy()
        del self.comif

    def is_valid(self, parameterName):
        
        if self.access_error(parameterName):
            return False
        else:
            return True 
        
    def access_error(self, parameterName):
        """ Check parameter for for update or apply errors
        
        """
        errors = []
        
        metadata = self.get_member(parameterName).metadata
        if 'p_update_error' in metadata:
            err = metadata['p_update_error']
            if err:
                errors.append(err)
            
        if 'p_apply_error' in metadata:
            err = metadata['p_apply_error']
            if err:
                errors.append(err)

        return errors
        
        
    def update_parameters(self, names=None, recursive = False):
        """ Update model parameters  from the COM object
        
        Parameters
        ----------
        attrs : iterable of str
            List of attribute names to update
            If None, then all model attributes will be updated
            
        """
        
        if names == None:
            
            names = list(self.iter_names())
        
        for name in names:
            
            fullname = '.'.join([self.fullname, name])
            
            #: Try getting value.  Set/clear get error flag
            try:
                val = getattr(self.comif, name)
                #logger.debug('Updating %s to %s') % (fullname, val)
                setattr(self, name, val)
                self.get_member(name).metadata['p_update_error'] = ''
                
            except Exception as e:
                
                self.get_member(name).metadata['p_update_error'] = str(e)
                logger.debug("Warning: could not update parameter '%s' from COM interface on model '%s'.\n %s" % (name, self.fullname, str(e)))
                
            
        if recursive:
            
            for child in self.children:
                
                child.update_parameters(recursive = recursive)

    def apply_parameters(self, names= None):
        """ Apply writable model parameters to the COM object
        
        Parameters are refreshed after application
        
        Parameters
        ----------
        attrs : iterable of str
            List of attribute names to update
            If None, then all model attributes will be updated
            
        """
        
        wnames = list(self.iter_names(writable = True))
        
        if names == None:
            
            names = wnames
        
        for name in names:
            
            fullname = '.'.join([self.fullname, name])
            
            if name in wnames:
            
                modelVal = getattr(self, name)
                #logger.debug('Applying %s to %s') % (fullname, modelVal)
                try:
                    setattr(self.comif, name, modelVal)
                    
                except Exception as e:
                    
                    self.get_member(name).metadata['p_apply_error'] = str(e)
                    logger.debug("Warning: Writable parameter '%s' could not be set to '%s'.\n %s" % (name, modelVal, str(e)))

                
                result = getattr(self.comif, name)
                if result != modelVal:
                    logger.debug("Warning: Attempt to set parameter %s to %s failed.  Actual value = %s" % (name, modelVal, result))
                
            else:
                
                raise Exception('Parameter name %s is not found or not writable' % name)

        self.update_parameters()

    def to_string(self, recursive = False):
        """ Create a pretty string from the Parameters in a ParameterModel 

        A re-implemented superclass method that also checks for COM access errors
         
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
        formatStr = "  {0} : {1}{2}"
        
        for name, val in self.iter_params():
            if self.is_valid(name):
                result.append(format(formatStr.format(name, str(val), '')))
            else:
                result.append(format(formatStr.format(name, str(val), ' (INVALID)' )))
                

        for child in self.children:
            
            result.append(child.to_string(recursive = recursive))
                
        return '\n'.join(result)
    
class DeviceParameterContainerModel(DeviceParameterModel):
    """ A DeviceParameterModel that ...
    
    """  
    Count = p_( Int() )    #: Number of objects
    Name  = p_(Value() )   #: Getter for object names
    Item  = p_(Value() )   #: Getter for COM object
    
    #: Container for repeatedmodels
    models = Dict()
    
    childFactory = Callable()
    
    def initialize(self):
        """ Discover and populate channel models
        
        """

        #: Intialize self.
        super(DeviceParameterContainerModel, self).initialize()
        
        channelDict = dict()
        
        for k in range(self.Count):
            
            name = self.Name(k+1)
            
            comif = self.Item(name)
            
            channelDict[name] = comif
       
            newChild =  self.childFactory(self, name=name)
            self.models[name] = newChild
        
            #: Initialize the new child
            newChild.initialize(comif= comif)
            
class ComMethod(Atom):
    restype    = Value()  #: Typed(ctypes.HRESULT, PyCSimpleType)
    methodname = Unicode()
    argtypes   = Tuple()
    paramflags = Tuple()
    idlflags   = Tuple()
    helptext   = Unicode()
    

def getComMethods(comif):
    """ Get methods of COM interface object
    
    TODO: Needs to recurse through inheritaged classes to get their methods too.
    
    Parameters
    ----------
    comif : comtypes.IUnknown (Base COM Interface object)
    
    Returns
    -------
    result: list[ComMethod]
    """
    
    result = []
    
    methods = comif._methods_
    
    for method in methods:
        #:restype, methodname, tuple(argtypes), tuple(paramflags), tuple(idlflags), helptext 
        comMethod = ComMethod(restype    = method[0],
                              methodname = method[1],
                              argtypes   = method[2],
                              paramflags = method[3],
                              idlflags   = method[4],
                              helptext   = method[5])
        result.append(comMethod)

    return result

def isComInterface(obj):
    return isinstance(obj, comtypes.IUnknown)


        
if __name__ == '__main__':
    
    pass