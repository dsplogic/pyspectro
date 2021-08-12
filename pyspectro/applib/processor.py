# ------------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
# ------------------------------------------------------------------------------


import threading
from atom.api import Atom, Typed, Value, Callable, Tuple, Dict, List, Float


import logging
logger = logging.getLogger(__name__)
    
from queue import Queue

import sys
if sys.version_info[0] == 3:
    EventClass = threading.Event
else:
    EventClass = threading._Event
    
class ProcessTask(Atom):
    """ An object representing a task

    """
    #: The callable to run when the task is executed.
    _callback = Callable()

    #: The args to pass to the callable.
    _args = Tuple()

    #: The keywords to pass to the callable.
    _kwargs = Dict()

    #: The result of invoking the callback.
    _result = Value()

    #: A callable to invoke with the result of running the task.
    _notify = Callable()

    def __init__(self, callback, args, kwargs):
        """ Initialize a ProcessTask.

        Parameters
        ----------
        callback : callable
            The callable to run when the task is executed.

        args : tuple
            The tuple of positional arguments to pass to the callback.

        kwargs : dict
            The dict of keyword arguments to pass to the callback.

        """
        self._callback = callback
        self._args = args
        self._kwargs = kwargs

    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
    def _execute(self):
        """ Execute the underlying task. 

        """
        self._result = self._callback(*self._args, **self._kwargs)
        if self._notify is not None:
            self._notify(self._result)

    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
    def notify(self, callback):
        """ Set a callback to be run when the task is executed.

        Parameters
        ----------
        callback : callable
            A callable which accepts a single argument which is the
            results of the task. It will be invoked immediate after
            the task is executed.

        """
        self._notify = callback

    def result(self):
        """ Returns the result of the task or None
        
        or raised an exception on execution.
        """
        return self._result



class CommandThread(Atom):
    """ A simple thread that accepts commands
    
    This class is intended to be sub-classed with
    a re-implemented self._main_loop method containing
    the thread functionality
    
    """
    #: Private storage for worker thread
    _thread       = Typed(threading.Thread)
    _terminate    = Typed(EventClass, ())
    
    #: Command queue
    _command      = Value(factory = Queue)
    
    #: Override in subclass with valid commands
    _valid_commands = []
    
    def initialize(self, thread_name = None):
        """ Create and start worker thread
        
        """
        logger.debug('Initializing %s' % (self.__class__.__name__))
        self._thread  = threading.Thread(target = self._main_loop, name = thread_name)
        self._thread.start()
        
    def terminate(self):
        """ Terminate worker thread and wait for it to terminate
        
        This method should be called prior to disconnecting the instrument.
        """
        if self._thread:
            logger.debug('Terminating %s' % (self.__class__.__name__))
            #: signal worker to finish processing
            self._terminate.set()
            
            #: Join worker thread
            self._thread.join()
            
            self._thread = None

    def send_command(self, cmd):
        """ Send command to worker thread
        
        """
        if cmd in self._valid_commands:
            self._command.put(cmd)
        else:
            logger.error('{0} ignored invalid command: {1}.  Must be one of {2}'.format(self.__class__.__name__, cmd, self._valid_commands))

    def _get_cmd(self):
        """ Check for new command without blocking
        
        Get command from queue.  Return empty string if queue is empty.
        """
        try:
            cmd = self._command.get(False)
        
        except:
            cmd = ''
            
        if cmd:
            logger.debug('{0} received command: {1}'.format(self.__class__.__name__, cmd))
            
        return cmd
    
    
    def _main_loop(self):
        """ Main worker thread

        Override with main thread loop
        
        Loop must terminate when _terminate event occurs
        Use _get_cmd() method to get commands
        """
        raise NotImplemented


    
class ThreadedProcessor(Atom):
    
    #: Incoming event to initiate the processor task
    start      = Typed(EventClass, ()) #: Start Processing data
    
    #: Outgoing Event produced when processor task is complete
    done       = Typed(EventClass, ()) #: Done Processing Data

    #: Private storage for worker thread
    _thread   = Typed(threading.Thread)
    _finish   = Typed(EventClass, ())
    
    #: The callable to run when the task is executed.
    _task = Callable()

    #: The args to pass to the task.
    _args = Tuple()

    #: The keywords to pass to the task.
    _kwargs = Dict()

    def __init__(self, task, args, kwargs):
        """ Initialize a Threaded Processor

        Parameters
        ----------
        task : callable
            Main processor task.

        args : tuple
            The tuple of positional arguments to pass to the task.

        kwargs : dict
            The dict of keyword arguments to pass to the task.

        """
        self._task = task
        self._args = args
        self._kwargs = kwargs
        
    def initialize(self, thread_name= None):
        """ Create and start worker thread
        
        """
        logger.debug('Initializing %s: %s' % (self.__class__.__name__, self._task.__name__))
        self._thread  = threading.Thread(target = self._worker, name = thread_name)
        self._thread.start()

    def terminate(self):
        """ Terminate worker thread and wait for it to terminate
        
        """
        if self._thread:

            logger.debug('Terminating %s: %s' % (self.__class__.__name__, self._task.__name__))
            
            #: signal worker to finish processing
            self._finish.set()
            
            #: Join worker thread
            self._thread.join()
            
            self._thread = None

    def _worker(self):
        """ Worker thread
        
        Worker thread.  Should handle start, finish events and produce done events
        """

        while not self._finish.is_set():
            
            #: Spend most time waiting for start
            started = self.start.wait(0.25)
            
            if started:
                
                self._task(*self._args, **self._kwargs)
                self.start.clear()
                self.done.set()
            
        self._finish.clear()


class SequentialProcessor(Atom):
    """ A Processor that performs a sequence of ThreadedProcessor tasks
    
    """

    #: List ot tasks to execute in sequential order
    tasks      = List(item = ThreadedProcessor)

    #: Command to initiate the processor task
    start      = Typed(EventClass, ()) #: Start Processing data
    
    #: Event produced when processor task is complete
    done       = Typed(EventClass, ()) #: Done Processing Data

    def __init__(self, tasks = []):
        """ Initialize a SequentialProcessor

        Parameters
        ----------
        task : callable
            Main processor task.

        args : tuple
            The tuple of positional arguments to pass to the task.

        kwargs : dict
            The dict of keyword arguments to pass to the task.

        """
        self.tasks = tasks
        
    def initialize(self):
        """ Schedule and initialize subtasks
        
        """
        self.tasks[0].start = self.start
        self.tasks[-1].done = self.done

        #: for all but first task
        for idx, task in enumerate(self.tasks):
            if idx > 0:
                task.start = self.tasks[idx-1].done 
        
        for task in self.tasks:
            task.initialize()
            

    def terminate(self):
        """ Terminate worker thread and wait for it to terminate
        
        This method should be called prior to disconnecting the instrument.
        """
        for task in self.tasks:
            task.terminate()
            
import time

class TimedProcessor(Atom):
    
    #: Timer interval
    _interval  = Float()
    
    #: Private storage for worker thread
    _thread   = Typed(threading.Thread)
    _finish   = Typed(EventClass, ())
    
    #: The callable to run when the task is executed.
    _task = Callable()

    #: The args to pass to the task.
    _args = Tuple()

    #: The keywords to pass to the task.
    _kwargs = Dict()

    def __init__(self, interval, task, args, kwargs):
        """ Initialize a Threaded Processor

        Parameters
        ----------
        interval : float
            Time between tasks (in seconds)
            
        task : callable
            Main processor task.

        args : tuple
            The tuple of positional arguments to pass to the task.

        kwargs : dict
            The dict of keyword arguments to pass to the task.

        """
        self._interval = interval
        self._task = task
        self._args = args
        self._kwargs = kwargs
        
    def start(self, thread_name= None):
        """ Create and start worker thread
        
        """
        logger.debug('Initializing %s: %s' % (self.__class__.__name__, self._task.__name__))
        self._thread  = threading.Thread(target = self._worker, name = thread_name)
        self._thread.start()

    def stop(self):
        """ Terminate worker thread and wait for it to terminate
        
        """
        if self._thread:

            logger.debug('Terminating %s: %s' % (self.__class__.__name__, self._task.__name__))
            
            #: signal worker to finish processing
            self._finish.set()
            
            #: Join worker thread
            self._thread.join()
            
            self._thread = None

    def _worker(self):
        """ Worker thread
        
        Worker thread.  Should handle start, finish events and produce done events
        """

        while not self._finish.is_set():
            
            #: Spend most time waiting for start
            time.sleep(self._interval)
            
            self._task(*self._args, **self._kwargs)
            
        self._finish.clear()

            

if __name__ == '__main__':

    import time

    def do_something(a, b, c=1, d=2):
        print('a = %s' % a)
        print('b = %s' % b)
        print('c = %s' % c)
        print('d = %s' % d)

        
    """ Test individual tasks
    
    """        
    task1 = ThreadedProcessor(do_something, args=(1,'bar'), kwargs = {'c': 'foo', 'd': 'bar'})
    task2 = ThreadedProcessor(do_something, args=(2,'bar'), kwargs = {'c': 'foo', 'd': 'bar'})
    task3 = ThreadedProcessor(do_something, args=(3,'bar'), kwargs = {'c': 'foo', 'd': 'bar'})
    
    sp = SequentialProcessor([task3, task2, task1])
    
    sp.initialize()
    sp.start.set()
    sp.done.wait()
    sp.start.set()
    sp.done.wait()
    sp.terminate()
    



    task4 = ThreadedProcessor(do_something, args=(4,'bar'), kwargs = {'c': 'foo', 'd': 'bar'})
    sp2 = SequentialProcessor([task4])
    sp2.initialize()
    sp2.start.set()
    sp2.done.wait()
    sp2.start.set()
    sp2.done.wait()
    sp2.terminate()

    def timed_call(s):
        print(s)
    
    print('Timed Processor')
    obj = TimedProcessor(1.0, timed_call, args = ('hi',), kwargs={})
    
    print('Starting')
    obj.start()
    
    time.sleep(4.9)
    
    print('Terminating')
    obj.stop()
    
    time.sleep(1)
    
    print('Restarting')
    obj.start()
    
    time.sleep(4.9)
    
    print('Terminating')
    obj.stop()
    