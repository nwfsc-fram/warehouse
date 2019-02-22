# pylint: disable=not-context-manager
# (see bug https://github.com/PyCQA/pylint/issues/782 )
"""
Module, providing a prefetched Warehouse model cache

The prefetch cache will periodically poll in the background for updates
 & refresh itself

Copyright (C) 2016 ERT Inc.
"""
import threading
import atexit
from copy import deepcopy
import logging

from api.resources.source.data import util as data_util
from ... import util #warehouse.util
from . import model

update_interval_seconds = 60
#TODO: consolidate duplicative CSW implementation

class NoDataError(ValueError):
    #raised when a Controller has not yet successfully fetch data
    pass

class Controller():
    """
    Encapsulates+configures a prefetch cache, with periodic auto-refresh

    #TODO: consolidate duplicative CSW implementation
    """

    def __init__(self, get_new_data_function
                 ,update_interval=update_interval_seconds
                 ,get_new_data_args=()
                 ,get_new_data_kwargs={}):
        """
        returns a new cache of output from 'get_new_data_function'

        Keyword Parameters:
        get_new_data_function  -- function Controller will use for the
          initial prefetch of data to cache, as well as for periodically
          obtaining new data to refresh the cache with
        update_interval  -- float, representing number of seconds
          Controller waits before polling for new data to refresh cache
          (Default: module-level 'update_interval_seconds' default)
        get_new_data_args  -- tuple of positional parameter arguments to
          be used with 'get_new_data_function' (Default: no parameters)
        get_new_data_kwargs  -- Dict of keyword parameters arguments to
          be used with 'get_new_data_function'

        >>> limited_testdata_generator = (i for i in range(5))
        >>> test_data_func = lambda: next(limited_testdata_generator)
        >>> from time import sleep
        >>> test_cache = Controller(test_data_func, 0.1)
        >>> test_cache.get_data()
        0
        >>> # Check cache
        >>> test_cache.get_data() # Expect previously cached value
        0
        >>> # Check that update polling works
        >>> test_extra_time = 0.09 #a bit of allowance, for threading
        >>> sleep(0.1 + test_extra_time)
        >>> test_cache.get_data()
        1
        >>> sleep(0.5)
        >>> test_cache.get_data()
        4
        >>> sleep(0.2) # check *any* additional period of time
        >>> test_cache.get_data() #expect final value to remain in cache
        4
        >>> test_cache.stop_update_thread()
        """
        self.logger = logging.getLogger(__name__)
        #logger, for this Controller instance

        self._poll_interval_seconds = update_interval
        self._cache_lock = threading.Lock()
        #Lock, synchronizing access to the cache object

        self._cached_data = None # cache object
        self._cache_unused = True #usage indicator

        self._update_thread = None
        #Background thread for performing scheduled updates to cache
        
        # instance attributes needed for fetching data to cache
        self._get_new_data = get_new_data_function
        self._args = get_new_data_args
        self._kwargs = get_new_data_kwargs
        
        
        atexit.register(self.stop_update_thread)
        #stop this Controller's polling, on Python interpreter exit
        
        self._fetch_and_schedule_update() #prefetch now!

    def stop_update_thread(self):
        """
        function to stop update loop

        >>> limited_testdata_generator = (i for i in range(5))
        >>> test_data_func = lambda: next(limited_testdata_generator)
        >>> from time import sleep
        >>> test_cache = Controller(test_data_func, 0.1)
        >>> test_cache.get_data()
        0
        >>> # Check that update polling works
        >>> test_extra_time = 0.09 #a bit of allowance, for threading
        >>> sleep(0.1 + test_extra_time)
        >>> test_cache.get_data()
        1
        >>> # Check polling stop
        >>> test_cache.stop_update_thread()
        >>> test_cache.get_data()
        1
        >>> sleep(0.3) # after *any* amount of time
        >>> test_cache.get_data() # cache should not change
        1
        """
        if self._update_thread is not None:
            self._update_thread.cancel()

    def get_data(self):
        """
        return copy of the cached data

        Exceptions:
        NoDataError  -- raised when model is None
        """
        with self._cache_lock:
            if self._cache_unused:
                raise NoDataError()
            # otherwise, return copy
            return deepcopy(self._cached_data)

    def _fetch_and_schedule_update(self):
        """
        schedule a new cache update
        """
        try:
            self._cache_data()
        except Exception as e:
            self.logger.info(e, exc_info=True)
        # assign a new task to the module-level thread variable
        self._update_thread = threading.Timer(self._poll_interval_seconds
                                        ,self._fetch_and_schedule_update)
        self._update_thread.start()

    def _cache_data(self):
        """
        update the data cache
        """
        new_data = self._get_new_data(*self._args, **self._kwargs) #This could take a few seconds
        with self._cache_lock:
            self._cached_data = new_data
            self._cache_unused = False #cache has been used now

_model_dump_kwargs = {'connection_func': util.get_dwsupport_connection}
#indicate how dump should connect to DB
prefetch_thread = Controller(model.dump
                             ,get_new_data_kwargs=_model_dump_kwargs)
#Module-level cache controller, for prefetch cache & periodic polling of DWSupport configuration model

def get_model():
    """
    return latest contests of the 'model.dump' prefetch thread
    """
    return prefetch_thread.get_data()
    
def stop_update_thread():
    """
    stop the module-level 'model.dump' prefetch thread
    """
    prefetch_thread.stop_update_thread()
