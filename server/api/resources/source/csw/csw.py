# pylint: disable=global-statement
"""
Module defining a Falcon resource which provides CSW protocol service

Also defined is an object (CswResponder) encapsulating a PyCSW server &
one, Global thread which runs in the background to keep the CSW metadata
repository fresh.

The CswResponder wrapper creates a pycsw configuration & a single pycsw
metadata repository database file (configuring them both with Warehouse
data) and then provides a pair of methods ('get_response',
'post_response') for processing CSW protocol HTTP requests.

The thread is started by instantiation of the Falcon resource object. It
is stopped by shutting down the Python interpreter (or manually evoking
'stop_update_thread()', e.g.: when testing, etc.)

Copyright (C) 2016 ERT Inc.
"""
import tempfile
import os
import os.path
from configparser import ConfigParser, SafeConfigParser
import shutil
import threading
import atexit
import contextlib
import errno
import logging

import falcon
from pycsw import server
import pycsw.core.admin
import pycsw.core.config
import filelock

from api import config_loader
from api.resources.source.warehouse import warehouse
from api.resources.source.csw import iso_metadata

route = 'csw'
#String representing the URI for this API endpoint

update_interval_seconds = 6*60
#frequency with which the PyCSW repository update thread runs

pycsw_config_template_filename = 'pycsw.cfg'
#filename of top-level API server config containing initial PyCSW settings

logger = logging.getLogger(__name__)
# Python logger, for this module

warehouse_csw_version = '1.0'
#version of the warehouse CSW Wrapper,for backward/forward compatibility

api_temp_subfolder_name = config_loader.get_api_config()['temp_subfolder_name']
# OS temporary subfolder configured for this API instance to use

pycsw_repo_filename = 'warehouse-{}-pycsw.sqlite3'.format(warehouse_csw_version)
#filename, for the PyCSW sqlite metadata repository
pycsw_temp_filename = pycsw_repo_filename+'.part'
#filename for a partial PyCSW repository, currently under construction

update_thread = threading.Thread()
#module thread that keeps the PyCSW repo up to date via a timer

temp_threading_lock = threading.Lock()
# lock to monitor thread access to the temporary PyCSW repo under construction

@atexit.register
def stop_update_thread():
    """
    function registered to stop update loop on Python interpreter exit
    """
    update_thread.cancel()

def schedule_update():
    """
    schedule a new PyCSW repository update
    """
    global update_thread
    # assign a new task to the module-level thread variable
    update_thread = threading.Timer(update_interval_seconds, update_csw_repo)
    update_thread.start() #start background thread

def update_csw_repo():
    """
    function to build new PyCSW repository then schedule a rebuild
    """
    # construct a new PyCSW sqlite store
    try:
        bogus_wsgi_environ = {'bogus': 'value'}#build_repo doesn't use environ
        with warehouse.get_source_model_session() as dwsupport_model:
            CswResponder(
                bogus_wsgi_environ
                ,api_temp_subfolder_name
            ).build_repo(dwsupport_model)
    except TempRepoLocked as e:
        msg = "Skipping CSW repo update, an update is already in-progress"
        logger.warning(msg)
        logger.debug(e.__cause__, stack_info=True)
    # schedule the next update
    schedule_update()

class TempRepoLocked(Exception):
    """
    Raised when temp is locked by another CswResponder.build_repo call
    """
    pass

class TempRepoFileLocked(OSError):
    """
    Raised when another process has an exclusive temp file lock
    """
    pass

class TempRepoThreadLocked(Exception):
    """
    Raised when another thread (of this interpreter) has locked temp
    """
    pass

class Csw():
    """
    Falcon resource object, providing CSW protocol service
    """

    def __init__(self):
        """
        Falcon resource object constructor, initializing module loop
        """
        schedule_update()

    def on_get(self, request, resp):
        """
        Falcon resource method, routing GET request details to PyCSW

        Keyword Parameters:
        request  -- Falcon request object
        resp  -- Falcon response object
        """
        # get response from our PyCSW wrapper
        wsgi_env = request.env
        status, xml_text = CswResponder(
            wsgi_env
            ,api_temp_subfolder_name
        ).get_response(
            request.uri
            ,request.params
        )

        # push response back out, through Falcon
        resp.content_type = 'text/xml'
        resp.status = status
        resp.body = xml_text


    def on_post(self, request, resp):
        """
        Falcon resource method, routing POST request details to PyCSW

        Keyword Parameters:
        request  -- Falcon request object
        resp  -- Falcon response object
        """
        content_length = request.content_length
        request_body = request.stream.read(content_length)

        # get response from our PyCSW wrapper
        wsgi_env = request.env
        status, xml_text = CswResponder(
            wsgi_env
            ,api_temp_subfolder_name
        ).post_response(request_body)

        # push response back out, through Falcon
        resp.content_type = 'text/xml'
        resp.status = status
        resp.body = xml_text

class CswResponder():
    """
    Utility class encapsulating PyCSW functionality

    per: https://github.com/geopython/pycsw/blob/447afc0/pycsw/server.py

    (the PyCSW API in use here was reverse engineered myself, by looking
      at the implementation of the 'server.py' class methods:
      Csw._write_response, Csw.dispatch, & Csw.dispatch_wsgi )
    """

    config_file_path = config_loader.get_server_file_path(pycsw_config_template_filename)

    config = None
    # ConfigParser object representing a usable pycsw configuration

    def __init__(self, environ, temp_subfolder_name):
        """
        Initialize PyCSW object with(manditory?) WSGI env values

        Keyword Parameters:
        environ  -- Dictionary, representing the Warehouse API server's
          PEP-3333 WSGI 'environ'

        >>> import datetime
        >>> CswResponder()
        Traceback (most recent call last):
           ...
        TypeError: __init__() missing 2 required positional arguments: 'environ' and 'temp_subfolder_name'
        >>> test_wsgi_environ = {'test': 'any_value'}
        >>> test_subfolder = 'warehouse-unittest1'
        >>> csw_responder = CswResponder(test_wsgi_environ, test_subfolder)
        >>> csw_responder.env == test_wsgi_environ
        True
        >>> os.path.exists(csw_responder._get_api_temp_path())
        True
        """
        # encapsulate WSGI configuration
        self.env = environ

        self.installation_subfolder_name = temp_subfolder_name
        if not os.path.exists(self._get_api_temp_path()):
            secure_path = tempfile.mkdtemp()
            os.rename(secure_path, self._get_api_temp_path())

        # generate a PyCSW config for current CSW-Wrapper version
        #based on template
        config_parser = ConfigParser()
        config_parser.read(self.config_file_path)

        # open the pycsw repository DB file
        repo_db_path = self._get_repo_path()
        repo_db_url = 'sqlite:///{}'.format(repo_db_path)
        config_parser['repository']['database'] = repo_db_url
        self.config = config_parser

    def get_config(self):
        """
        returns protected ConfigParser representing initial PyCSW config

        Repeated calls to this method will always return the same
        values. Any changes made to the returned protected config will
        not modify the original configuration.

        >>> import datetime
        >>> from pprint import pformat
        >>> test_wsgi_environ = {'test': 'any_value'}
        >>> test_subfolder = 'warehouse-unittest1'
        >>> test_responder = CswResponder(test_wsgi_environ, test_subfolder)
        >>> config1 = test_responder.get_config()
        >>> config1['NewSection'] = {'key':'value'}
        >>> 'NewSection' in test_responder.get_config()
        False
        """
        # convert Config into a depricated 'SafeConfigParser' for pycsw
        pycsw_config = SafeConfigParser()
        pycsw_config.read_dict(self.config)
        return pycsw_config

    def _get_api_temp_path(self):
        """
        Returns String path to OS temp subfolder API is configured with
        """
        os_temp_folder = tempfile.gettempdir()

        return os.path.join(os_temp_folder, self.installation_subfolder_name)

    def _get_repo_path(self):
        """
        Returns String path of PyCSW repository database
        """
        return os.path.join(self._get_api_temp_path(), pycsw_repo_filename)

    def _get_temp_repo_path(self):
        """
        Returns String path of partial PyCSW repo under construction
        """
        return os.path.join(self._get_api_temp_path(), pycsw_temp_filename)

    @contextlib.contextmanager
    def _file_lock_context(self, file_path):
        """
        Context manager obtaining an exclusive lock on referenced file

        Lock is automatically released when context ends or if this
        Python process is killed externally.

        Keyword Parameters:
        file_path  -- String, representing path to the file to be locked

        Exceptions:
        TempRepoFileLocked  -- raised if the referenced file is already
          locked by another process.

        >>> from multiprocessing import Process
        >>> from time import sleep
        >>> import signal
        >>> test_wsgi_environ = {'test': 'any_value'}
        >>> test_subfolder = 'warehouse-unittest1'
        >>> test_responder = CswResponder(test_wsgi_environ, test_subfolder)
        >>> test_output = []
        >>> with tempfile.NamedTemporaryFile() as test_file:
        ...    # Check locking once
        ...    with test_responder._file_lock_context(test_file.name):
        ...        test_output.append('Locked once')
        >>> test_output
        ['Locked once']
        >>> test_output = []
        >>> with tempfile.NamedTemporaryFile() as test_file:
        ...    # Check locking twice
        ...    with test_responder._file_lock_context(test_file.name):
        ...        test_output.append('Locked once')
        ...        with test_responder._file_lock_context(test_file.name):
        ...            test_output.append('Locked twice?')
        Traceback (most recent call last):
           ...
        api.resources.source.csw.csw.TempRepoFileLocked
        >>> test_output #Expect only 1x entry
        ['Locked once']
        >>> # Check locking, when another process holds lock
        >>> test_output = []
        >>> with tempfile.NamedTemporaryFile() as test_file:
        ...     def unit_test_get_lock():
        ...         with test_responder._file_lock_context(test_file.name):
        ...             sleep(1.1) #Hold lock for 1100 ms
        ...     locking_process = Process(target=unit_test_get_lock)
        ...     locking_process.start()
        ...     sleep(0.1) # wait for process to start running
        ...     # Try to relock, via the main testing process
        ...     with test_responder._file_lock_context(test_file.name):
        ...         test_output.append('Locked twice?')
        Traceback (most recent call last):
           ...
        api.resources.source.csw.csw.TempRepoFileLocked
        >>> locking_process.join()
        >>> test_output
        []
        >>> # Check lock release, when locking processed killed
        >>> test_output = []
        >>> with tempfile.NamedTemporaryFile() as test_file:
        ...     def unit_test_get_lock():
        ...         with test_responder._file_lock_context(test_file.name):
        ...             sleep(1.1) #Hold lock for 1100 ms
        ...     locking_process = Process(target=unit_test_get_lock)
        ...     locking_process.start()
        ...     os.kill(locking_process.pid, signal.SIGKILL)
        ...     sleep(0.1) # wait for process to die
        ...     # Try to relock, via the main testing process
        ...     with test_responder._file_lock_context(test_file.name):
        ...         test_output.append('Lock successful')
        >>> locking_process.join()
        >>> test_output
        ['Lock successful']
        """
        #per: https://pypi.python.org/pypi/filelock
        lock = filelock.FileLock(file_path)
        try:
            lock.acquire(timeout=0.05) #closest thing to Nonblocking?
        except filelock.Timeout as e:
            raise TempRepoFileLocked() from e
        yield
        #Automatically release the lock, when context ends
        lock.release()

    @contextlib.contextmanager
    def _lock_temp_repo(self):
        """
        Context manager obtaining a exclusive lock on the temp repo file

        Lock is automatically released when context ends or if this
        Python process is killed externally.

        Exceptions:
        TempRepoFileLocked  -- raised if the temporary PyCSW repository
          is already locked by another process.
        """
        file_path = self._get_temp_repo_path()
        with self._file_lock_context(file_path) as opened:
            yield opened

    def build_repo(self, dwsupport_model):
        """
        utility method to replace CSW repo with a newly constructed one

        Keyword Parameters:
        dwsupport_model -- dictionary representing the current DWSupport
          configuration.

        Exceptions:
        TempRepoLocked  -- raised when PyCSW repo is under construction
          by another thread or process & is not available for this call.

        >>> import datetime
        >>> test_wsgi_environ = {'test': 'any_value'}
        >>> test_model = { 'tables': [{ 'name': 'test_fact','updated': datetime.datetime(2016, 4, 25, 15, 31, 43)
        ...                            ,'bounds': '60,-100,40,-120'
        ...                            ,'project': 'trawl', 'years': '1998-2015'
        ...                            ,'description': 'abstract in English', 'title': 'Trawl survey catch'
        ...                            ,'contact':
        ...                             'Name: FRAM Data Team <nmfs.nwfsc.fram.data.team@noaa.gov>'
        ...                            ,'rows': 301530, 'keywords': 'pacific,trawl,survey,marine'
        ...                            ,'restriction': 'otherRestrictions', 'usage_notice':
        ...                             'Courtesy: Northwest Fisheries Science Center, NOAA Fisheries'
        ...                            ,'update_frequency': 'continual', 'uuid': None}]
        ...               ,'projects': [{ 'name': 'trawl'
        ...                             ,'uuid': '90A-BC-DEF1'}] }
        >>> test_subfolder = 'warehouse-unittest1'
        >>> csw_responder = CswResponder(test_wsgi_environ, test_subfolder)
        >>> csw_responder.build_repo(test_model)
        >>> #Check if initialization has a db file URL
        >>> 'database' in csw_responder.config['repository']
        True
        >>> db_url = csw_responder.config['repository']['database']
        >>> db_url[0:10] #Check what URL starts with
        'sqlite:///'
        >>> prefix_known, repo_db_path = db_url.split('sqlite:///')
        >>> #Check what the URI filename looked like
        >>> repo_db_path[-14:] #(last few characters)
        '-pycsw.sqlite3'
        >>> os.path.exists( #Check if initialization created the repo DB
        ...     repo_db_path)
        True
        >>> os.path.exists( #check that temp repo has been removed
        ...     csw_responder._get_temp_repo_path())
        False
        """
        try:
            # Make certain no other threads are already building
            temp_threading_lock.acquire(blocking=False)
            build_config = self.get_config()
            # open a temporary pycsw repository DB file & obtain lock
            temp_repo_path = self._get_temp_repo_path()
            temp_existed_before_lock = os.path.exists(temp_repo_path)
            with self._lock_temp_repo(): #lock repo with this Process ID
                if temp_existed_before_lock:
                    # Clear any existing file contents
                    truncate_file = 'w'
                    with open(temp_repo_path, truncate_file):
                        pass #file is truncated, by 'open'
                temp_repo_url = 'sqlite:///{}'.format(temp_repo_path)
                #per:https://github.com/geopython/pycsw/blob/f6907e6/bin/pycsw-admin.py#L258
                repo_table = build_config['repository']['table']
                server_home = build_config['server']['home']
                pycsw.core.admin.setup_db(temp_repo_url, repo_table, server_home)
                #populate db with Warehouse metadata
                #per:https://github.com/geopython/pycsw/blob/f6907e6/bin/pycsw-admin.py#L264
                csw_static_config = pycsw.core.config.StaticContext()
                #get ISO 19139 metadata for every Warehoused data item
                temp_xml_dir_path = tempfile.mkdtemp(prefix='warehouse-'
                                                     ,dir=self._get_api_temp_path()
                                                     ,suffix='-pycsw')
                try:
                    for source in [source_table for source_table
                                   in dwsupport_model['tables']]:
                        iso_xml = iso_metadata.geographic_metadata(source, dwsupport_model)
                        #write XML to a file, because it's the only thing pycsw understands
                        xml_file_descriptor, xml_path = tempfile.mkstemp(
                            dir=temp_xml_dir_path
                            ,suffix='.xml')
                        os.close(xml_file_descriptor)#Unneeded readonly file descriptor
                        with open(xml_path, 'w') as xml_file:
                            xml_file.write(iso_xml)
                    pycsw.core.admin.load_records(
                        csw_static_config
                        ,temp_repo_url
                        ,repo_table
                        ,temp_xml_dir_path
                        ,False #process directory recursively
                        ,False #force interactive confirmation
                    )
                finally:
                    shutil.rmtree(temp_xml_dir_path)#clean up XML temp files
                #move temporary db file to final location
                shutil.move(temp_repo_path, self._get_repo_path())
            temp_threading_lock.release()
        except TempRepoFileLocked as e:
            #Raise error,temp is already locked by another call to build_repo
            raise TempRepoLocked() from e
        except TempRepoThreadLocked as e:
            #Raise error,another thread is calling build_repo
            raise TempRepoLocked() from e

    def _build_repo_if_missing(self):
        """
        utility method to build repo if one does not yet exist

        Exceptions:
        TempRepoLocked  -- raised when PyCSW repo is under construction
          by another thread or process & is not available for this call.
        """
        try:
            with open(self._get_repo_path()) as test:
                pass
        except FileNotFoundError:
            # repo seems to be missing, build new repo & respond
            with warehouse.get_source_model_session() as dwsupport_model:
                self.build_repo(dwsupport_model)

    def get_response(self, request_url, query_string_parameters):
        """
        Utility function to retrieve GET response from PyCSW

        Keyword Parameters:
        request_url  -- String representation of the full-URL for this
          HTTP GET request
        query_string_parameters  -- Dictionary, representing the
          'request_url' query string key/value pairs

        Exceptions:
        TempRepoLocked  -- raised when PyCSW repo is under construction
          by another thread or process & is not available for this call.
        """
        pycsw_config = self.get_config()
        self._build_repo_if_missing()
        csw = server.Csw(pycsw_config, self.env)
        csw.requesttype = 'GET'
        csw.request = request_url
        csw.kvp = query_string_parameters
        return csw.dispatch()


    def post_response(self, request_body):
        """
        Utility function to retrieve POST response from PyCSW

        Keyword Parameters:
        request_body  -- Bytes representing the body of the HTTP POST

        Exceptions:
        TempRepoLocked  -- raised when PyCSW repo is under construction
          by another thread or process & is not available for this call.
        """
        pycsw_config = self.get_config()
        self._build_repo_if_missing()
        csw = server.Csw(pycsw_config, self.env)
        csw.requesttype = 'POST'
        csw.request = request_body
        return csw.dispatch()
