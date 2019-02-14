"""
Module, providing a DAO api for accessing warehouse management authorizations

Copyright (C) 2017 ERT Inc.
"""
from datetime import datetime

import sqlalchemy

from api.resources.source.warehouse.support import dto_util

SCHEMA = "dwauth"
# authorization schema

TABLE = "management_authorization"
# auth table,containing the list of authorizations

class ValidateTypeError(TypeError):
    """
    Raised when type of a Warehouse authorization is not Dict-like
    """
    pass
class ValidateMissingValue(ValueError):
    """
    Raised when a required, warehouse authorization attribute is absent.
    """
    pass
class ValidateUnexpectedValue(ValueError):
    """
    Raised when an unrecognized, authorization attribute is encountered.
    """
    pass

def validate(management_authorization):
    """
    validate if referenced object conforms to this module's api for
    warehouse authorizations.

    Keyword Parameters:
    management_authorization -- dictionary representing an API authorization

    Exceptions:
    ValidateTypeError -- raised when authorization parameter is not a
      dictionary
    ValidateMissingValue -- authorization parameter is incomplete
    ValidateUnexpectedValue -- authorization parameter is malformed

    >>> import datetime
    >>> from copy import deepcopy
    >>> auth1 = {'user_id':'uid=salvador.dali,ou=People,o=noaa.gov'}
    >>> validate(auth1)
    True
    >>> validate('{"user_id":"test"}')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.management_authorization.ValidateTypeError: <class 'str'>
    >>> partial = deepcopy(auth1); removed = partial.pop('user_id')
    >>> validate(partial)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.management_authorization.ValidateMissingValue: user_id
    >>> extra = deepcopy(auth1); extra['shouldnt_be_here!'] = True
    >>> validate(extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.management_authorization.ValidateUnexpectedValue: shouldnt_be_here!
    """
    try:
        authorization_keys = management_authorization.keys()
    except AttributeError as e: #Error, table is not dict-like
        raise ValidateTypeError(type(management_authorization)) from e
    # verify object contents
    expected_keys = ['user_id']
    for key in expected_keys: #check that *all* attributes are present
        if key not in authorization_keys:
            raise ValidateMissingValue(key)
    for key in authorization_keys: #check for any non-standard attributes
        if key not in expected_keys:
            raise ValidateUnexpectedValue(key)
    # must be good!
    return True

def get_all(db_url=None, connection_func=None):
    """
    retrive the current list of authorization from the db

    Keyword Parameters:
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArgument  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> get_all()
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection(db_url, connection_func)
    # prepare statement, to get table metadata
    select_statement = ('SELECT \n'
                        '   a.user_id \n'
                        'FROM {auth_schema}.{authorization_table} a \n'
                       ).format(auth_schema=SCHEMA, authorization_table=TABLE)
    try:
        result = connection.execute(select_statement)
        management_authorizations = list()
        for row in result:
            management_authorization = dict(row) #make a real dict, so we can pprint() etc.
            validate(management_authorization)
            management_authorizations.append(management_authorization)
        return management_authorizations
    except:
        raise
    finally:
        connection.close()

def save(management_authorizations, db_url=None, connection_func=None):
    """
    persists a list of one (or more) authorizations, to the warehouse db

    Keyword Parameters:
    management_authorizations  --  list of authorizations
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> import datetime
    >>> empty_list = []
    >>> save([])
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # prepare statement, to write out the authorizations
    template = """INSERT into {auth_schema}.{authorization_table} (
                   user_id
                  ) values (
                   %(user_id)s --use the same key name, as the type dictionary
                  )"""
    insert_statement = template.format(auth_schema=SCHEMA, authorization_table=TABLE)
    # insert! -- directly use authorization dictionaries for binds
    dto_util.exec_base(management_authorizations, validate, insert_statement, db_url=db_url
                       ,connection_func=connection_func)
