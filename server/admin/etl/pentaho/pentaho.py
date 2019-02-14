"""
Module providing utility functions for managing Pentaho data-integration

Copyright (C) 2016-2018 ERT Inc.
"""
from contextlib import contextmanager
import logging
import tempfile
import os.path
import filelock
import shutil
import zipfile
import platform
import stat
import threading
import subprocess
from pprint import pformat
from collections import deque
from xml.etree import ElementTree as etree
from time import sleep

import requests

from . import configure

logger = logging.getLogger(__name__)

DATA_INTEGRATION_ZIPFILE = 'pdi-ce-8.0.0.0-28.zip'

CONFIG_TEMPLATE_NAME = 'carte-master-config.xml'

EXECUTION_TEMPLATE_NAME = 'job_execution_configuration_template.xml'

KETTLE_CONNECTION_PROPERTIES = 'kettle.properties_ConnectionDetails'

def log_stdout_from_subprocess(process_object):
    """
    function implementing a workerloop, logging STDOUT from a subprocess
    """
    while True:
        exit_code = process_object.poll()
        if exit_code is not None: #then, process has exited
            # print all available output & exit
            for unlogged_line in process_object.stdout.readlines():
                logger.info(unlogged_line.rstrip())
            return
        # otherwise, process is still running: log output lines
        unlogged_line = process_object.stdout.readline()
        logger.info(unlogged_line.rstrip())

def java_encode_pw(encr_script_path, plaintext_pw):
    """
    Return 'plantext_pw' encoded with Pentaho "encr" Java tool

    Keyword Parameters:
    encr_script_path  -- String, representing absolute path to Java
      encr launching script
    plaintext_pw  -- String, representing the value to encode
    """
    with tempfile.TemporaryFile() as encr_output, tempfile.TemporaryFile() as encr_error:
            encr_exit_code = subprocess.call( [encr_script_path, '-carte', plaintext_pw]
                                               ,stderr=encr_error
                                               ,stdout=encr_output
                                               ,universal_newlines=True)
            encr_output.seek(0)#return current read/write positions to start
            encr_error.seek(0)
            if encr_exit_code not in [0]:
                msg = (  pformat(encr_output.readlines())
                       + pformat(encr_error.readlines()) )
                raise Exception(encr_exit_code, msg) #TODO: define custom class
            binary_pw_plus_newline = deque(iter(encr_output), maxlen=1).pop()
            encoded_pw = binary_pw_plus_newline.decode('utf-8').rstrip()
    return encoded_pw

class CarteControllerTempdirPrefixStarted(RuntimeError):
    """
    'start' evocation with same 'tempdir_prefix' value is still running
    """
    pass

class CarteControllerLoadJobsError(Exception):
    """
    base exception, thrown by CarteController.load_jobs
    """
    pass

class CarteControllerRegistrationConnectionError(CarteControllerLoadJobsError):
    """
    Error connecting to Pentaho carte server, to register a job
    """
    pass

class CarteControllerRegistrationHttpError(CarteControllerLoadJobsError):
    """
    Pentaho carte server returned an HTTP error during job registration
    """
    pass

class CarteControllerRegistrationError(CarteControllerLoadJobsError):
    """
    carte server returned a Pentaho XML error during job registration
    """
    pass

class CarteControllerStartHttpError(CarteControllerLoadJobsError):
    """
    Pentaho carte server returned an HTTP error during job startup
    """
    pass

class CarteController:
    """
    Object abstracting a Pentaho "Carte" Java server process
    
    Provides methods for interacting (starting, stopping, loading, etc.)
    with the Carte process.
    """

    def __init__(self, port, host, username, password, key
            ,https_keystore_path, https_keystore_pw, https_openssl_pw):
        """
        Construct a controller instance according to config parameters

        Keyword Parameters:
        port  -- integer, representing TCP port assigned for this Carte
          server.
        host  -- String, representing network adapter Carte server is
          to listen on
        username  -- String, representing name for the Carte admin login
        password  -- String, representing the Carte admin login password
        key  -- String, representing KETTLE_PASSWORD_ENCODER_PLUGIN aes
          encryption key
        https_keystore_path  -- String, representing path to HTTPS java
          keystore
        https_keystore_pw  -- String, representing encoded password for
          java keystore
        https_openssl_pw  -- String, representing encoded password for
          OpenSSL secret key located inside the HTTPS keystore

        >>> CarteController()
        Traceback (most recent call last):
           ...
        TypeError: __init__() missing 8 required positional arguments: 'port', 'host', 'username', 'password', 'key', 'https_keystore_path', 'https_keystore_pw', and 'https_openssl_pw'
        >>> fake_key = '010001BE01ACE100010001000100010001000100010001000100010001000100'
        >>> fake_jks = '/foo/path/keystore.jks'
        >>> test_object = CarteController( 45678, '0.0.0.0', 'test'
        ...                               ,'myDogsBirthDate', fake_key
        ...                               ,fake_jks ,'OBF:1234'
        ...                               ,'OBF:abcd')
        >>> isinstance(test_object, CarteController)
        True
        """
        self.carte_host = host
        self.carte_port = port
        self.carte_url = "https://{}".format(self.carte_host)

        self.https_keystore_path = https_keystore_path
        self.https_keystore_pw = https_keystore_pw
        self.https_openssl_pw = https_openssl_pw

        self.carte_user = username
        # String, representing username for the carte instance
        self.carte_pw = password
        self.connection_credentials_key = key

    def status(self):
        """
        Returns XML status document, from the external Carte webserver

        >>> fake_key = '010001BE01ACE100010001000100010001000100010001000100010001000100'
        >>> fake_jks = '/foo/path/keystore.jks'
        >>> c = CarteController( 45678, '0.0.0.0', 'test'
        ...                     ,'myDogsBirthDate', fake_key, fake_jks
        ...                     ,'OBF:1234', 'OBF:abcd')
        >>> c.status()
        False
        """
        url = '{}:{}/kettle/status?xml=y'.format(self.carte_url, self.carte_port)
        try:
            response = requests.get(url, auth=(self.carte_user, self.carte_pw), verify=False)
            if response.status_code == 200:
                return response.content
        except requests.exceptions.ConnectionError as e:
            logger.warning(e)
        return False

    def stop(self):
        """
        Stops external Carte webserver process

        >>> fake_key = '010001BE01ACE100010001000100010001000100010001000100010001000100'
        >>> fake_jks = '/foo/path/keystore.jks'
        >>> c = CarteController( 45678, '0.0.0.0', 'test'
        ...                     ,'myDogsBirthDate', fake_key
        ...                     ,fake_jks ,'OBF:1234', 'OBF:abcd')
        >>> c.stop() # doctest: +ELLIPSIS
        Traceback (most recent call last):
           ...
        requests.exceptions.ConnectionError: HTTPSConnectionPool(host='0.0.0.0', port=45678): Max retries exceeded with url: /kettle/stopCarte?xml=y (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x...>: Failed to establish a new connection: [Errno 111] Connection refused',))
        """
        url = '{}:{}/kettle/stopCarte?xml=y'.format(self.carte_url, self.carte_port)

        response = requests.get(url, auth=(self.carte_user, self.carte_pw), verify=False)
        if response.status_code != 200:
            raise Exception(response.content) #TODO: implement a custom class

    def start(self, tempdir_suffix, java_opts):
        """
        Start java-based Carte webserver in an external process

        Keyword Parameters:
        tempdir_suffix  -- String, representing an OS temp dir subfolder
          where the Carte server files should be unpacked
        java_opts  -- String, representing PENTAHO_DI_JAVA_OPTIONS
          environmental variable value to be passed to startup script
          
        Exceptions:
        CarteControllerTempdirPrefixStarted  -- raised when a 'start'
          (with the same tempdir_suffix) is still running on this host.

        >>> from time import sleep
        >>> unittest_string = '45678-unitTest_pentaho_start'
        >>> fake_key = '010001BE01ACE100010001000100010001000100010001000100010001000100'
        >>> fake_jks = '/foo/path/keystore.jks'
        >>> c = CarteController( 45678, '0.0.0.0', 'test'
        ...                     ,'myDogsBirthDate', fake_key
        ...                     ,fake_jks ,'OBF:1234', 'OBF:abcd')
        >>> c.start(tempdir_suffix=unittest_string, java_opts='-Xms1024m -Xmx2048m -XX:MaxPermSize=256m')
        Traceback (most recent call last):
           ...
        FileNotFoundError: [Errno 2] No such file or directory: '/foo/path/keystore.jks'
        >>> unpacked_dir = os.path.join( #clean up
        ...     tempfile.gettempdir(),'warehouse-carte-{}'.format(unittest_string)
        ... )
        >>> shutil.rmtree(unpacked_dir)
        >>> # Confirm Java process is not running
        >>> c.stop() # doctest: +ELLIPSIS
        Traceback (most recent call last):
           ...
        requests.exceptions.ConnectionError: HTTPSConnectionPool(host='0.0.0.0', port=45678): Max retries exceeded with url: /kettle/stopCarte?xml=y (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x...>: Failed to establish a new connection: [Errno 111] Connection refused',))
        """
        # configure a multiprocess lock
        #per: https://pypi.python.org/pypi/filelock
        pentaho_dir_prefix = 'warehouse-carte-'
        pentaho_dir = os.path.join(
            tempfile.gettempdir(), pentaho_dir_prefix+tempdir_suffix
        )
        pentaho_started_lockfile = pentaho_dir+'.lock'
        lock = filelock.FileLock(pentaho_started_lockfile)

        already_running = self.status()
        if already_running:
            try:
                # see if lock is available
                lock.acquire(timeout=0.05) #closest thing to Nonblocking?
                # lock was available (controlling process died?)      
                # try and stop any previously started instances
                seconds = 0.1 #TODO: improve subprocess control (maybe allow them to stay running?)
                self.stop()
                sleep(seconds)
                try:
                    self.stop() #check once more
                except requests.exceptions.ConnectionError:
                    # expected! Java process definitely should be unreachable
                    pass
                lock.release() #stop cleanup
            except filelock.Timeout as failed_to_acquire_lock:
                # controlling process is still alive - already running
                return True

        try: #TODO: refactor similar csw.py impl
            lock.acquire(timeout=0.05) #closest thing to Nonblocking?
        except filelock.Timeout as e:
            msg = "Pentaho startup ({}) already in-progress".format(tempdir_suffix)
            error = CarteControllerTempdirPrefixStarted(msg)
            raise error from e
        # unpack Pentaho Data-Integration program pack
        pentaho_module_dir = os.path.dirname(__file__)
        zipfile_module_subfolder = 'java'
        data_integration_filepath = os.path.join(
            pentaho_module_dir, zipfile_module_subfolder, DATA_INTEGRATION_ZIPFILE
        )
        with zipfile.ZipFile(data_integration_filepath) as data_integration:
            secure_path = tempfile.mkdtemp() #TODO: refactor similar csw.py impl
            if os.path.exists(pentaho_dir):
                shutil.rmtree(pentaho_dir)
            os.rename(secure_path, pentaho_dir)
            data_integration.extractall(pentaho_dir)
        # install additional JARs
        jar_module_subfolder = 'jars' # source folders
        jar_module_path = os.path.join(pentaho_module_dir, jar_module_subfolder)
        lib_subfolder = 'lib'
        plugin_subfolder = 'plugins'
        data_integration_subfolder = 'data-integration' # dest. folders
        jar_destination_base_path = os.path.join(
            pentaho_dir, data_integration_subfolder
        )
        lib_destination_path = os.path.join(jar_destination_base_path, lib_subfolder)
        plugin_destination_path = os.path.join(jar_destination_base_path, plugin_subfolder)
        jar_source_destination_pairs = [ #map sources to destinations
            (os.path.join(jar_module_path, lib_subfolder), lib_destination_path)
            ,(os.path.join(jar_module_path, plugin_subfolder), plugin_destination_path)
        ]
        for jar_source, jar_destination in jar_source_destination_pairs:
            #traverse the sources, flattening their contents & copying to dests
            for dir_name, subdirs, files in os.walk(jar_source):
                for file_name in files:
                    if file_name.endswith('.jar'):
                        source_jar_path = os.path.join(dir_name, file_name)
                        shutil.copy2(source_jar_path, jar_destination)
        # prepare launch script
        script_suffix = 'sh'
        if any(platform.win32_ver()):
            #script names are different on Windows OS
            script_suffix = 'bat'
        carte_start_script = os.path.join(
            pentaho_dir, data_integration_subfolder, 'carte.{}'.format(script_suffix)
        )
        # set Java options
        os.environ['PENTAHO_DI_JAVA_OPTIONS'] = java_opts
        # set environment variable (Needed for encr.sh via Apache)
        os.environ['KETTLE_HOME'] = os.path.join(pentaho_dir, data_integration_subfolder)
        # set permissions
        owner_read_write_execute_group_others_read_only = (
             stat.S_IEXEC|stat.S_IREAD|stat.S_IWRITE
            |stat.S_IRGRP
            |stat.S_IROTH
        )
        os.chmod(carte_start_script, owner_read_write_execute_group_others_read_only)
        spoon_script = os.path.join( #TODO: refactor, to reduce code duplication
            pentaho_dir, data_integration_subfolder, 'spoon.{}'.format(script_suffix)
        )
        os.chmod(spoon_script, owner_read_write_execute_group_others_read_only)
        encr_script = os.path.join( #TODO: refactor, to reduce code duplication
            pentaho_dir, data_integration_subfolder, 'encr.{}'.format(script_suffix)
        )
        os.chmod(encr_script, owner_read_write_execute_group_others_read_only)
        # in KETTLE_HOME, configure KETTLE_PASSWORD_ENCODER_PLUGIN
        key = self.connection_credentials_key
        # and DB connection properties
        db_details_path = os.path.join(pentaho_module_dir, KETTLE_CONNECTION_PROPERTIES)
        with open(db_details_path) as details_file:
            db_details = details_file.read()
        kettle_properties_conf = configure.generate_properties_text(key, db_details)
        kettle_home_path = os.path.join(pentaho_dir, data_integration_subfolder
                                        ,'.kettle')
        os.mkdir(kettle_home_path)#NB: must run before launch config/encr tool
        kettle_properties_path = os.path.join(kettle_home_path, 'kettle.properties')
        with open(kettle_properties_path, 'w') as kettle_properties_file:
            kettle_properties_file.write(kettle_properties_conf)
        # deploy keystore file to pentaho directory
        keystore_filename = os.path.basename(self.https_keystore_path)
        keystore_path = os.path.join(
            pentaho_dir, data_integration_subfolder, keystore_filename)
        shutil.copyfile(self.https_keystore_path, keystore_path)
        # prepare launch config
        template_path = os.path.join(pentaho_module_dir, CONFIG_TEMPLATE_NAME)
        with open(template_path) as config_template:
            template_xml = config_template.read()
        config_xml = configure.generate_config_text(
             xml_template = template_xml
            ,host = self.carte_host
            ,port = str(self.carte_port)
            ,user = self.carte_user
            ,encoded_pw = java_encode_pw(encr_script, self.carte_pw)
            ,https_keystore_path = keystore_path# path to deployed file
            ,obf_jks_pw = self.https_keystore_pw
            ,obf_openssl_pw = self.https_openssl_pw)
        config_path = os.path.join(
            pentaho_dir, data_integration_subfolder, 'carte-configuration.xml')
        with open(config_path, 'w') as config_file:
            config_file.write(config_xml)
        # start server
        stdbuf_command = ['stdbuf', '-oL'] #force Line-level output buffering
        # (pipe redirection of stdout otherwise uses a 4096byte default buffer,
        #  which is way too large/slow for logging)
        carte_command = [carte_start_script, config_path]
        java_process = subprocess.Popen(stdbuf_command + carte_command
                                        ,stdout=subprocess.PIPE
                                        ,stderr=subprocess.STDOUT
                                        ,universal_newlines=True)
        background_java_log_thread = threading.Thread(
             target = log_stdout_from_subprocess
            ,args = (java_process, )
        )
        background_java_log_thread.start()
        # start job loader thread
        job_source = os.path.join(pentaho_module_dir, 'jobs')
        zip_extension = '.zip'
        job_zippath_name_tuples = list()
        for file_name in os.listdir(job_source):
            if file_name.lower().endswith(zip_extension):
                name_without_extension = file_name[:-1*len(zip_extension)]
                zipfile_path = os.path.join(job_source, file_name)
                zippath_and_name = (zipfile_path, name_without_extension)
                job_zippath_name_tuples.append(zippath_and_name)
        def job_loader():
            # Simple worker function, to wait for Carte startup then load jobs
            while not self.status():
                sleep(15)
            self.load_jobs(job_zippath_name_tuples)
        job_loader_thread = threading.Thread(target = job_loader)
        job_loader_thread.start()
        def unlock_poller():
            # Simple worker loop, to unlock the tempfiles when Carte exits
            while True:
                if java_process.poll() is not None:
                    lock.release()
                    return
                sleep(0.5)
        unlock_thread = threading.Thread(target = unlock_poller)
        unlock_thread.start()

    def dump_jobs(self):
        """
        Returns list of job names, loaded in the external Carte server

        >>> fake_key = '010001BE01ACE100010001000100010001000100010001000100010001000100'
        >>> fake_jks = '/foo/path/keystore.jks'
        >>> c = CarteController( 45678, '0.0.0.0', 'test'
        ...                     ,'myDogsBirthDate', fake_key
        ...                     ,fake_jks ,'OBF:1234', 'OBF:abcd')
        >>> c.dump_jobs()
        Traceback (most recent call last):
           ...
        Exception: Server Connection Error
        """
        status_string = self.status()
        try:
            xml_status = etree.fromstring(status_string)
        except TypeError as e:
            raise Exception('Server Connection Error') from e #TODO: implement as custom class
        jobs = []
        for job_status in xml_status.iter('jobstatus'):
            job_dict = { 'name': job_status.find('jobname').text
                        ,'id': job_status.find('id').text
                        ,'status': job_status.find('status_desc').text
                       }
            jobs.append(job_dict)
        return jobs

    @contextmanager
    def _tmp_copy_of_job_zipfile(self, job_zipfile_path):
        """
        Context, returning a temporary writable copy of referenced file

        This is needed to edit zipfiles, as the 'pentaho/jobs/' dir is
        not writable by the Apache user.

        >>> fake_key = '010001BE01ACE100010001000100010001000100010001000100010001000100'
        >>> fake_jks = '/foo/path/keystore.jks'
        >>> c = CarteController( 45678, '0.0.0.0', 'test'
        ...                     ,'myDogsBirthDate', fake_key
        ...                     ,fake_jks ,'OBF:1234', 'OBF:abcd')
        >>> any_file = __file__ #This file (not a zip, but works).
        >>> with c._tmp_copy_of_job_zipfile(any_file) as temp:
        ...   os.path.basename(temp.name).startswith("warehouse-carte-45678-")
        ...   temp.name.endswith("-pentaho.py-add-execution-config.tmp")
        ...   temp.read()[:10]
        True
        True
        b'\"\"\"\\nModule'
        """
        job_name = os.path.basename(job_zipfile_path)
        prefix = 'warehouse-carte-{}-'.format(self.carte_port)
        suffix = '-{}-add-execution-config.tmp'.format(job_name)
        with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix) as temp:
            shutil.copy2(job_zipfile_path, temp.name)
            yield temp

    def load_jobs(self, job_tuples):
        """
        loads Pentaho job exports to external Carte server & returns job IDs

        Keyword Parameters:
        job_tuples  -- list of string tuples, representing paths to Pentaho
          job export files and the names of the jobfile within the export.

        >>> test_prefix = 'unittest-admin.etl.pentaho.load_jobs'
        >>> fake_key = '010001BE01ACE100010001000100010001000100010001000100010001000100'
        >>> fake_jks = '/foo/path/keystore.jks'
        >>> with tempfile.NamedTemporaryFile(prefix=test_prefix, suffix='.zip') as tmp:
        ...     c = CarteController( 45678, '0.0.0.0', 'test'
        ...                         ,'myDogsBirthDate', fake_key
        ...                         ,fake_jks ,'OBF:1234', 'OBF:abcd')
        ...     c.load_jobs([(tmp.name, 'foo_job.kjb')])
        []
        """
        url = '{}:{}/kettle/registerPackage/?xml=y&type=job&load='.format(self.carte_url, self.carte_port)
        start_url = '{}:{}/kettle/startJob/?xml=y&id='.format(self.carte_url, self.carte_port)

        responses = list()

        module_path = os.path.dirname(__file__)
        execution_config = os.path.join(module_path,EXECUTION_TEMPLATE_NAME)
        for job_zipfile_path, job_name in job_tuples:
            try:
                # add Execution configuration (Spoon exports don't include these)
                with self._tmp_copy_of_job_zipfile(job_zipfile_path) as zipfile_copy:
                    with zipfile.ZipFile(zipfile_copy.name, 'a') as writable_zipfile:
                        archive_conf_filename = '__job_execution_configuration__.xml'
                        writable_zipfile.write(execution_config, archive_conf_filename)
                    with open(zipfile_copy.name, 'rb') as export_zipfile:
                        # upload
                        try:
                            response = requests.post(url+job_name
                                                    ,auth=(self.carte_user, self.carte_pw)
                                                    ,data=export_zipfile, verify=False)
                        except requests.exceptions.ConnectionError as e:
                            raise CarteControllerRegistrationConnectionError() from e
                        xml_result = etree.fromstring(response.content).find('result').text
                        if xml_result == 'ERROR':
                            xml_message = etree.fromstring(response.content).find('message').text
                            raise CarteControllerRegistrationError(xml_message)
                if response.status_code != 200:
                    raise CarteControllerRegistrationHttpError(response.content)
                # retrieve assigned Carte job id & set job to the 'running' state
                job_id = etree.fromstring(response.content).find('id').text
                start_response = requests.get(start_url+job_id
                                              ,auth=(self.carte_user, self.carte_pw), verify=False)
                if start_response.status_code != 200:
                    raise CarteControllerStartHttpError(start_response.content)
                responses.append(start_response.content)
            except CarteControllerLoadJobsError as e:
                #if one Job fails to load, log it & try next job
                logger.error(e)
                continue
        return responses
