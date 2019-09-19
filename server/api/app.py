# pylint: disable=global-statement
"""
Module defining a WSGI application 'app', implementing the Warehouse API

Copyright (C) 2015, 2016 ERT Inc.
"""
import logging
import os.path
import tempfile
import ast
from threading import Thread
from pprint import pformat

import falcon
from beaker.middleware import SessionMiddleware
import sqlalchemy

from api import config_loader, aes, json
from api.resources import (
    p3p
    ,login
    ,logout
    ,user
    ,usage_info
)
from .resources.saml import (
    metadata as saml_metadata
    ,service_provider
)
from .resources.external import login as external_login
from api.resources.source import (
    source
    ,parameters as source_parameters
    ,variables
    ,inport_metadata
)
from api.resources.source.csw import iso_metadata, csw
from api.resources.source.selection import selection
from api.handlers import middleware
from admin.etl.pentaho import pentaho

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

# export only the Wsgi app (not other module global vars).
__all__ = ['app']

api_ver = 'v1'

pentaho_started = False
#module-level flag, tracking whether Java subprocess has been started

pentaho_controller = None
#object, abstracting a communication channel to the background Java subprocess

api_temp_subfolder_name = os.path.join(
     tempfile.gettempdir() #TODO: refactor, with similar CSW/carte implementations
    ,config_loader.get_api_config()['temp_subfolder_name'])
# OS temporary subfolder configured for this API instance to use

app = falcon.API( after=[middleware.crossdomain, middleware.p3p_header])

def get_datatables_editor_exception(falcon_http_error):
    """
    Make Falcon HTTPError 'to_json' method DataTables Editor compatible

    Returns the referenced HTTPError, with modifications

    Keyword Parameters:
    falcon_http_error  -- Falcon HTTPError exception

    >>> # Check unmodified Exception
    >>> plain = falcon.HTTPError(status=200, description='Plain!')
    >>> plain.to_json()
    '{\\n    "description": "Plain!"\\n}'
    >>> # Check modified
    >>> out = get_datatables_editor_exception(plain)
    >>> out.to_json()
    '{"data": [], "error": "{\\'description\\': \\'Plain!\\'}"}'
    """
    falcon_http_error.to_json = lambda:json.dumps({
         'error': pformat(falcon_http_error.to_dict()) #value must be String
        ,'data': [] #data must be present & be an empty Array
    }, sort_keys=True)
    return falcon_http_error

def handle_http_error(exception, req, resp, params):
    """
    Simple Falcon responder to log exceptions, before responding to web client

    >>> normal_exception = falcon.HTTPNotFound(description='friendly msg')
    >>> normal_exception.__cause__ = Exception('technical info')
    >>> handle_http_error( normal_exception, None, None, None)
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPNotFound
    >>> unhandled_exception = Exception("I was not expected!")
    >>> handle_http_error( unhandled_exception, None, None, None)
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPInternalServerError
    """
    if not isinstance(exception, falcon.HTTPError):
        #Warning! exception is not an HTTP response, be careful not to expose
        # security sensitive internal information
        logging.exception( Exception("Unsanitized exception occurred!", exception))#TODO: make this a locally defined class
        sanitized = falcon.HTTPInternalServerError(title='500',description="Please try again")
        raise get_datatables_editor_exception(sanitized)
    # else, intentionally raised (safe) web error
    #internally log cause
    if exception.__cause__:
        logging.exception(exception.__cause__)
    logging.exception(exception) #Falcon stack does not seem to include cause.
    # raise safe exception to client
    raise get_datatables_editor_exception(exception)

def wrap_app_with_session_middleware(wsgi_app):
    """
    Install Middleware for session establishment around referenced app

    Keyword Parameters:
    wsgi_app  -- WSGI application to add middleware to & return
    """
    cache_subfolder = 'session_cache' #Folder, for storing user sessions
    cache_subfolder_path = os.path.join(api_temp_subfolder_name, cache_subfolder)
    if not os.path.exists(cache_subfolder_path):
        os.makedirs(cache_subfolder_path) #Create (Beaker cant make subfolder)

    logger = logging.getLogger(wrap_app_with_session_middleware.__name__)
    #Logger, for this function

    cache_filename = 'beaker.sqlite3'
    session_cache_path = os.path.join(cache_subfolder_path, cache_filename)
    session_cache_url = "sqlite:///{}".format(session_cache_path)

    max_session_days = 90 #Cookie invalid after 90days

    session_opts = {
        'session.timeout': 90*60 #90min timeout
        ,'session.cookie_expires': max_session_days*24*3600
        ,'session.auto': True #Automatically save session
        ,'session.key': "api.session.id"
        ,'session.type': "ext:database" #store in sqlitedb,so all Apache process can see
        ,'session.lock_dir': cache_subfolder_path
        ,'session.url': session_cache_url
        ,'session.sa_opts': {'extend_existing': True} #fix mod_wsgi error when 2+ processes init
        #,'session.secure': True #TODO: enable this property to force SSL sessions
    }
    # attempt to clean up old/expired sessions
    over_limit = 1 #Don't actually delete until 1 full day over the limit
    total = max_session_days+over_limit
    cleanup_sql = "DELETE FROM beaker_cache WHERE accessed < datetime('now', :modifier)"
    delete_older_than_modifier = '-{} days'.format(total)
    try:
        # this might fail, if db doesnt exist
        engine = sqlalchemy.create_engine(session_cache_url)
        engine.execute(cleanup_sql, [delete_older_than_modifier])
    except Exception as e:
        # but dont worry, cleanup will be retried next time WSGI app launches
        logger.info(e, exc_info=True)
        # ignore error, & continue
    # install the session middleware!
    return SessionMiddleware(wsgi_app, session_opts)

def start_etl_scheduler():
    """
    Start the Java extract, transform & load scheduler subprocess
    """
    global pentaho_started, pentaho_controller
    conf = config_loader.get_api_config()
    ciphertext = ast.literal_eval(conf['etl.pentaho.ciphertext'])#TODO: refactor similar api.resources.source.data.py implementation
    key = ast.literal_eval(conf['etl.pentaho.ciphertext_key'])
    try:
        pentaho_controller = pentaho.CarteController(port=conf['etl.pentaho.port'], host=conf['etl.pentaho.host'], username=conf['etl.pentaho.username'], password=aes.decode(ciphertext, key), key=conf['etl.pentaho.connection_credentials_key'], https_keystore_path=conf['etl.pentaho.https.keystore'], https_keystore_pw=conf['etl.pentaho.https.jks_pw'], https_openssl_pw=conf['etl.pentaho.https.openssl_pw'])
        pentaho_controller.start(tempdir_suffix=conf['etl.pentaho.port']
                                 ,java_opts=conf['etl.pentaho.java.opts'])
        pentaho_started = True
    except TypeError as e:
        startup_exception = Exception('Failed to start Carte etl-scheduler', e) #TODO: define custom class
        logging.warning(startup_exception, exc_info=True)
    except pentaho.CarteControllerTempdirPrefixStarted as e:
        logging.warning(e, exc_info=True)

def get_uri_template(resource_path):
    """
    Utility function, to build an endpoint's Falcon uri_template string

    >>> get_uri_template('source')
    '/v1/source'
    >>> get_uri_template('p3p.xml')
    '/v1/p3p.xml'
    """
    return ''.join( ['/', api_ver, '/', resource_path])

def get_selection_uri_template():
    """
    Utility function, to build Selection endpoint's Falcon uri_template string

    >>> get_selection_uri_template()
    '/v1/source/{source_id}/selection.{type}'
    """
    str_source_uri = get_uri_template(source.str_route)

    path_selection = selection.str_route
    param_id = source_parameters.source_id
    param_type = selection.str_param_type
    str_selection_uri = ''.join(
        ['/{', param_id, '}/', path_selection, '{', param_type, '}']
    )
    return str_source_uri+str_selection_uri

def get_variables_uri_template():
    """
    Utility function, to build Variables endpoint Falcon uri_template string

    >>> get_variables_uri_template()
    '/v1/source/{source_id}/variables'
    """
    str_source_uri = get_uri_template(source.str_route)

    path_variables = variables.str_route
    param_id = source_parameters.source_id
    str_variables_uri = ''.join( [ '/{', param_id, '}/', path_variables])
    return str_source_uri+str_variables_uri

def get_inport_uri_template():
    """
    build InPort XML Metadata endpoint Falcon uri_template string

    >>> get_inport_uri_template()
    '/v1/source/{source_id}/metadata.xml'
    """
    source_uri = get_uri_template(source.str_route) #base URL

    endpoint_name = inport_metadata.route
    param_id = source_parameters.source_id #accept data set ID, as path param
    inport_suffix = '/{'+param_id+'}/'+endpoint_name
    return source_uri+inport_suffix

def get_csw_uri_template():
    """
    build Falcon uri_template string for ISO-19139 Metadata endpoint

    >>> get_csw_uri_template()
    '/v1/source/{source_id}/metadata.iso'
    """
    source_uri = get_uri_template(source.str_route) #base URL

    endpoint_name = iso_metadata.route
    param_id = source_parameters.source_id #accept data set ID, as path param
    inport_suffix = '/{'+param_id+'}/'+endpoint_name
    return source_uri+inport_suffix

def get_saml_uri_template(resource_path):
    """
    build Falcon uri_template string for SAML Service Provider endpoints

    >>> get_saml_uri_template('metadata')
    '/v1/saml/metadata'
    """
    saml_path = get_uri_template('saml/') #base URL
    return saml_path+resource_path

# add Exception handlers
app.add_error_handler(Exception, handle_http_error)

# map RESTful resources, to the URIs
app.add_route(get_uri_template(login.route), login.Login())
app.add_route(get_uri_template('external/')+external_login.route, external_login.Login())
app.add_route(get_uri_template(logout.route), logout.Logout())
app.add_route(get_uri_template(user.route), user.User())
app.add_route(get_saml_uri_template(saml_metadata.route), saml_metadata.EntityDescriptor())
app.add_route(get_saml_uri_template(service_provider.route), service_provider.SamlEndpoint())
app.add_route(get_uri_template(usage_info.route), usage_info.Help())
app.add_route( get_uri_template(source.str_route), source.Source())
app.add_route(get_uri_template(csw.route), csw.Csw())
app.add_route(get_inport_uri_template(), inport_metadata.Metadata())
app.add_route(get_csw_uri_template(), iso_metadata.Metadata())
app.add_route( get_uri_template(p3p.str_route), p3p.PolicyReferenceFile())

str_selection_uri = get_selection_uri_template()
app.add_route( str_selection_uri, selection.Selection())

app.add_route( get_variables_uri_template(), variables.Variables())

# add request middleware
app = wrap_app_with_session_middleware(app)

# fork off a thread, to perform Pentaho Java server background init
#launcher_thread = Thread(target = start_etl_scheduler)
#launcher_thread.start()
