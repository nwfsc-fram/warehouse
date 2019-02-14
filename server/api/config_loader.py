"""
Utility module, for obtaining Warehouse config settings from .ini files

Copyright (C) 2015, 2016 ERT Inc.
"""
import configparser
import os.path
import api

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov, "

server_filename = 'server.ini'
server_heading = 'all_servers'

def get_api_config():
    """
    Returns dict, representing server config file 'all_server' settings

    >>> from pprint import pprint
    >>> d = get_api_config()
    >>> isinstance(d, dict)
    True
    >>> d['id']
    'all_servers'
    """
    return get_heading_dict( server_filename, server_heading)

class HeadingNotFoundError(KeyError):
    """
    Exception raised when requested heading cannot be found in specified .ini
    """
    pass

def _build_datasource_dict( str_heading, dict_config_entry):
    """
    returns Metadata dict describing warehoused FRAM dataset's ETL config entry

    >>> entry1 = {'name':'My Great Dataset','query':'select 1 from dual'
    ... ,'db_file':'x.ini'}
    >>> d = _build_datasource_dict( 'great.Data1', entry1)
    >>> d['id']
    'great.Data1'
    >>> d['name']
    'My Great Dataset'
    >>> entry2 = {'name':'My Great Dataset','query':'select 1 from dual'
    ... ,'db_file':'x.ini'}
    >>> d = _build_datasource_dict('trawl.SurVEY', entry2)
    >>> d['id']
    'trawl.SurVEY'
    >>> d['name']
    'My Great Dataset'
    """
    dict_datasource = {}
    for key in dict_config_entry.keys():
        dict_datasource[key] = dict_config_entry[key]
    dict_datasource['id'] = str_heading
    return dict_datasource

def get_server_file_path(filename):
    """
    Returns string, representing the path to a file in the server/ dir

    Keyword Arguments:
    filename - string, representing the name of a top-level API config file
    """
    #get path to top-level 'server/' dir
    api_package_dir = os.path.dirname(api.__file__)
    dir_containing_config_and_api = os.path.join(api_package_dir, '..')
    path_to_file = os.path.join(dir_containing_config_and_api, filename)
    return path_to_file

def get_list_of_heading_dicts( filename):
    """
    Returns list of dicts, representing named headings in referenced .ini file

    Keyword Arguments:
    filename - string, representing the name of a top-level API config file

    >>> l1 = get_list_of_heading_dicts('db_config.ini')
    >>> isinstance(l1, list)
    True
    >>> len( l1)
    1
    >>> dict_first_in_list = l1[0]
    >>> 'id' in dict_first_in_list.keys()
    True
    >>> dict_first_in_list['id']
    'warehouse'
    """
    #Open the indicated top-level .ini
    path_to_config = get_server_file_path(filename)
    config_parser = configparser.RawConfigParser()
    config_parser.read( path_to_config)
    #retrieve all Sections & place contents into a dict
    list_of_heading_dicts = []
    for str_heading in config_parser.keys():
        if str_heading != 'DEFAULT':
            config_section = config_parser[str_heading]
            list_of_heading_dicts.append( _build_datasource_dict( str_heading, config_section))
    return list_of_heading_dicts

def get_list_of_etl_dicts():
    """
    Returns list of dicts, representing Data Source Extract/Transform details
    
    >>> l = get_list_of_etl_dicts()
    >>> isinstance( l, list)
    True
    """
    return get_list_of_heading_dicts('etl_config.ini')

def get_heading_dict( filename, str_heading):
    """
    obtain properties, from referenced top-level config file, & heading

    Exceptions:
    HeadingNotFoundError -- raised when heading cannot be found on disk,
        including due to missing or empty files (e.g.: no headings at all)

    >>> d = get_heading_dict('db_config.ini', 'warehouse')
    >>> isinstance( d, dict)
    True
    >>> d['sqlalchemy.pool_recycle'] #expect Proactive timeout,SERVER_03
    '3600'
    >>> d = get_heading_dict('db_dwsupport.ini', 'warehouse')
    >>> isinstance( d, dict)
    True
    >>> str_unlikely_heading = 'utProbablyNotReal1234'
    >>> d = get_heading_dict('db_dwsupport.ini', str_unlikely_heading)
    Traceback (most recent call last):
      ...
    api.config_loader.HeadingNotFoundError: 'utProbablyNotReal1234'
    >>> str_nonexistent_file = 'utProbablyNotReal1234.ini'
    >>> d = get_heading_dict( str_nonexistent_file, 'warehouse')
    Traceback (most recent call last):
      ...
    api.config_loader.HeadingNotFoundError: 'warehouse'
    """
    list_of_heading_dicts = get_list_of_heading_dicts( filename)
    #retrieve specified Section
    for dict_heading in list_of_heading_dicts:
        if dict_heading['id'] == str_heading:
            return dict_heading
    else:
        raise HeadingNotFoundError( str_heading)
