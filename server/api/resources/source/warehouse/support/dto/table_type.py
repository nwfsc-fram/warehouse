"""
Module, providing a DAO api for accessing metadata on warehoused table types.

warehoused tables belong to one of two types: fact, or dimension tables

Copyright (C) 2016 ERT Inc.
"""
from api.resources.source.warehouse.support import dto_util
import sqlalchemy

TABLE = "table_type"
# Warehouse table,containing the warehouse table types

class ValidateTypeError(TypeError):
    """
    Exception raised when the type of a Warehouse table type is not a
    dictionary.
    """
    pass
class ValidateUnexpectedValue(ValueError):
    """
    Raised when an unrecognized, warehouse table type attribute is encountered.
    """
    pass

def get_all():
    """
    returns list of all accepted table types.

    >>> get_all()
    ['fact', 'dimension', 'dimension role']
    """
    return ['fact', 'dimension', 'dimension role']

def validate( table_type):
    """
    validate if referenced object conforms to this module's api for warehouse
    table type.

    Keyword Parameters:
    table_type -- dictionary representing a warehoused table type

    Exceptions:
    ValidateTypeError -- raised when table_type is not a String
    ValidateUnexpectedValue -- raised when table_type is malformed

    >>> from copy import deepcopy
    >>> validate( 'fact')
    True
    >>> validate( 'dimension')
    True
    >>> validate( {'fact':'dict'})
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table_type.ValidateUnexpectedValue: {'fact': 'dict'}
    >>> validate( 'UnrecognizedType')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table_type.ValidateUnexpectedValue: UnrecognizedType
    """
    type_names = get_all()
    if table_type not in type_names:
        raise ValidateUnexpectedValue( table_type)
    # must be good!
    return True

def save(types, db_url=None, connection_func=None):
    """
    persists a list of one (or more) table types, to the warehouse database

    Keyword Parameters:
    types  --  list of table types
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    ValidateTypeError -- raised when table_type is not a String
    ValidateUnexpectedValue -- raised when table_type is malformed

    >>> empty_list = []
    >>> save( [])
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # write out the types -- first, prepare a statement
    template = 'INSERT into {schema}.{table} (type_name) values (%s);'
    insert_statement = template.format(schema=dto_util.SCHEMA, table=TABLE)    
    # next compose a one list of bind parameters, for each row to be inserted
    insert_binds = [ [t] for t in types]
    # insert!
    dto_util.exec_base( insert_binds, validate, insert_statement, db_url=db_url
                       ,connection_func=connection_func)
