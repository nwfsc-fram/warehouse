"""
Module, providing a DAO api for accessing warehouse table authorizations

Copyright (C) 2016 ERT Inc.
"""
from datetime import datetime

import sqlalchemy

from api.resources.source.warehouse.support import dto_util
from api.resources.source.warehouse.support.dto import (
    table
   ,project
)

SCHEMA = "dwauth"
# authorization schema

TABLE = "table_authorization"
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

def validate(authorization):
    """
    validate if referenced object conforms to this module's api for
    warehouse authorizations.

    Keyword Parameters:
    authorization -- dictionary representing a selection authorization

    Exceptions:
    ValidateTypeError -- raised when authorization parameter is not a
      dictionary
    ValidateMissingValue -- authorization parameter is incomplete
    ValidateUnexpectedValue -- authorization parameter is malformed

    >>> import datetime
    >>> from copy import deepcopy
    >>> auth1 = {'user_id':'uid=salvador.dali,ou=People,o=noaa.gov'
    ...         ,'project': 'mail'
    ...         ,'table': 'thank_you_notes_fact'}
    >>> validate(auth1)
    True
    >>> validate('{"user_id":"test"}')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table_authorization.ValidateTypeError: <class 'str'>
    >>> partial = deepcopy(auth1); removed = partial.pop('project')
    >>> validate(partial)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table_authorization.ValidateMissingValue: project
    >>> extra = deepcopy(auth1); extra['shouldnt_be_here!'] = True
    >>> validate(extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table_authorization.ValidateUnexpectedValue: shouldnt_be_here!
    """
    try:
        authorization_keys = authorization.keys()
    except AttributeError as e: #Error, table is not dict-like
        raise ValidateTypeError(type(authorization)) from e
    # verify object contents
    expected_keys = ['user_id','project','table']
    for key in expected_keys: #check that *all* attributes are present
        if key not in authorization_keys:
            raise ValidateMissingValue(key)
    for key in authorization_keys: #check for any non-standard attributes
        if key not in expected_keys:
            raise ValidateUnexpectedValue(key)
    # must be good!
    return True

def get_all( db_url=None, connection_func=None):
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
                        '  ,p.name AS "project" \n'
                        '  ,t.name AS "table" \n'
                        'FROM {auth_schema}.{authorization_table} a \n'
                        '   INNER JOIN {support_schema}.{table_table} t \n'
                        '     ON a.table_id = t.table_id \n'
                        '   INNER JOIN {support_schema}.{project_table} p \n'
                        '     ON t.project_id = p.project_id \n'
                       ).format(auth_schema=SCHEMA, authorization_table=TABLE
                                ,support_schema=dto_util.SCHEMA
                                ,project_table=project.TABLE
                                ,table_table=table.TABLE)
    try:
        result = connection.execute(select_statement)
        authorizations = list()
        for row in result:
            authorization = dict(row) #make a real dict, so we can pprint() etc.
            validate(authorization)
            authorizations.append(authorization)
        return authorizations
    except:
        raise
    finally:
        connection.close()

def save(authorizations, db_url=None, connection_func=None):
    """
    persists a list of one (or more) authorizations, to the warehouse db

    Keyword Parameters:
    authorizations  --  list of authorizations
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
                  ,table_id
                  ,nda_signed_date
                  ) values (
                   %(user_id)s --use the same key name, as the type dictionary
                  ,(SELECT project_id
                      FROM {support_schema}.{project_table}
                      WHERE name=%(project)s )
                  ,(SELECT contact_id
                      FROM {support_schema}.{table_table}
                      WHERE name=%(table)s
                        AND project_id=(SELECT project_id
                                        FROM {support_schema}.{project_table}
                                        WHERE name=%(project)s ))
                  ,'1970-01-01'
                  )"""
    insert_statement = template.format(auth_schema=SCHEMA, authorization_table=TABLE
                                       ,support_schema=dto_util.SCHEMA
                                       ,project_table=project.TABLE
                                       ,table_table=table.TABLE
                                      )
    # insert! -- directly use authorization dictionaries for binds
    dto_util.exec_base(authorizations, validate, insert_statement, db_url=db_url
                       ,connection_func=connection_func)
