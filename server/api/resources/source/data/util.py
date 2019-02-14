"""
Utility module, encapsulating useful Data support functions

Copyright (C) 2016 ERT Inc.
"""
import ast
import logging

import sqlalchemy

from api import (
    aes
    ,config_loader
)
    

class ConfigPasswordCiphertextError(TypeError):
    # raised when .ini ciphertext encoding db password is bad/missing
    pass
class ConfigDbConnectError(ValueError):
    # Database connect error while using .ini config file settings
    pass

def get_engine_from_config(api_config_file_name):
    """
    returns SQLAlchemy Engine, from referenced top-level API conf file
    """
    db_config = config_loader.get_heading_dict(api_config_file_name
                                                   ,'warehouse')
    # decode encrypted pw
    key = ast.literal_eval(db_config['ciphertext_key'])
    encoded_pw = ast.literal_eval(db_config['ciphertext'])
    try:
        decoded = aes.decode(encoded_pw, key)
        # build a connection URL with the decoded pw
        url_without_pw = db_config['sqlalchemy.url']
        db_url = sqlalchemy.engine.url.make_url(url_without_pw)
        db_url.password = decoded
        # add new URL to config
        db_config['sqlalchemy.url'] = str(db_url)
    except TypeError as e:
        exception = ConfigPasswordCiphertextError(api_config_file_name, e)
        logging.error(exception, stack_info=True)
    # instantiate engine from config
    engine = sqlalchemy.engine_from_config(db_config)
    return engine

dict_engines_by_filename = {
     'db_config.ini': get_engine_from_config('db_config.ini')
    ,'db_dwsupport.ini': get_engine_from_config('db_dwsupport.ini')
    ,'db_dwsensitive.ini': get_engine_from_config('db_dwsensitive.ini')
}
"""
Module-level collection of SQL connection engines

Collection is created once, at module import, from the top-level API
connection properties config files.
"""

def _get_source_connection(dict_source):
    """
    utility method,returning a SqlAlchemy Connection to the requested dataset

    >>> source = {'db_file':'db_config.ini'}
    >>> con = _get_source_connection( source)
    Traceback (most recent call last):
      ...
    api.resources.source.data.util.ConfigDbConnectError: db_config.ini
    """
    #obtain SQL engine instance
    db_config = dict_source['db_file']
    engine = dict_engines_by_filename[db_config]
    #open connection
    try:
        connection = engine.connect()
    except sqlalchemy.exc.SQLAlchemyError as e:
        raise ConfigDbConnectError(db_config) from e

    return connection
