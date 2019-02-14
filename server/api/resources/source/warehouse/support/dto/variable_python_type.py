"""
Module, providing a DAO api for accessing metadata on warehoused python_types.

Python object types are associated with warehoused Variables (measured values &
 dimensional attributes), as a convenience - for binding values into SQLAlchemy
querys, without first having to connect/query the table to determine the column
type.

Copyright (C) 2016 ERT Inc.
"""
import datetime
import decimal

import sqlalchemy

from api.resources.source.warehouse.support import (
    dto_util
    ,discover
)

TABLE = "variable_python_type"
# Warehouse table,containing the Python constructor names

class VariablePythonTypeTypeError(TypeError):
    """
    Exception raised when the type of a Warehouse python_type is not a
    dictionary.
    """
    pass
class VariablePythonTypeUnexpectedValue(ValueError):
    """
    Raised when an unrecognized, warehouse python_type attribute is encountered.
    """
    pass

class LookupNullType(TypeError):
    """
    Raised when get_by_lookup() encounters a database column with 'Null' type
    """
    pass

def get_all():
    """
    returns list of all Python type constructors we need to use to bind values
    in to warehouse SQL queries.

    >>> get_all()
    ['str', 'float', 'int', 'datetime.datetime']
    """
    return ['str','float','int','datetime.datetime']

def get_by_lookup( table_name, column_name, db_url=None, connection=None):
    """
    returns the name of the Python type constructor, that corresponds to the
     referenced table & column.

    Keyword Parameters:
    table_name  --  String representing name of the warehouse table, where
      column is located
    column_name  --  String representing name of the warehouse column who's
      Python type constructor name is to be returned.
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection  -- SQLAlchemy connection (Optional, if provided, will override
      db_url)

    Exceptions:
    ConnectionMissingArguments  -- raised if neither connection or db_url
      parameter is specified.

    >>> get_by_lookup( 'any_table', 'some_field')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection( db_url, connection)
    # fetch table metadata
    try:
        # obtain python type of column via SQLAlchemy reflection
        metadata = sqlalchemy.MetaData() #any needed lookup Tables will be
                                         # listed in metadata.tables
        table = sqlalchemy.Table(table_name, metadata
            , autoload=True # reflect columns, as defined in the db
            , autoload_with=connection
            , schema=discover.SCHEMA)
        for column in table.columns:
            if column.name == column_name:
                try:
                    constructor = column.type.python_type
                except NotImplementedError as e:
                    if isinstance(column.type, sqlalchemy.sql.sqltypes.NullType):
                        msg = ("Unknown database type [maybe PostGIS?]."
                               " Table$Column: '{}${}'"
                              ).format(table_name, column_name)
                        raise LookupNullType(msg)
                    raise
                # match SQLAlchemy constructor, to the one we use internally
                python_type_constructor = None
                if issubclass(constructor, int):
                    python_type_constructor = 'int'
                #FIXME: transition away from float.. Decimal is more user friendly
                if issubclass(constructor, (float, decimal.Decimal)):
                    python_type_constructor = 'float'
                if issubclass(constructor, str):
                    python_type_constructor = 'str'
                if issubclass(constructor, (datetime.datetime,datetime.time)):
                    python_type_constructor = 'datetime.datetime'
                if python_type_constructor is None:
                    msg = "Unable to map '{}' to Warehouse type".format(constructor)
                    raise Exception(msg) #TODO: refactor into custom class
                validate( python_type_constructor)
                return python_type_constructor
        else:
            msg = "No columns defined, for table '{}'".format(table_name)
            raise Exception( msg) #TODO: refactor into custom class
    except:
        raise
    finally:
        connection.close()

def validate( variable_python_type):
    """
    validate if referenced object conforms to this module's api for warehouse
    python_types.

    Keyword Parameters:
    variable_python_type -- dictionary representing a warehoused Python type

    Exceptions:
    VariablePythonTypeTypeError -- raised when variable_python_type is not a
      String
    VariablePythonTypeUnexpectedValue -- raised when variable_python_type is
      malformed

    >>> from copy import deepcopy
    >>> validate( 'str')
    True
    >>> validate( 'float')
    True
    >>> validate( 'int')
    True
    >>> validate( 'datetime.datetime')
    True
    >>> validate( {'python_type':'dict'})
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.variable_python_type.VariablePythonTypeTypeError: <class 'dict'>
    >>> validate( 'UnrecognizedType')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.variable_python_type.VariablePythonTypeUnexpectedValue: UnrecognizedType
    """
    # verify object type
    if not isinstance( variable_python_type, str):
        raise VariablePythonTypeTypeError( type(variable_python_type))
    # verify object contents
    expected_constructor_names = get_all()
    if variable_python_type not in expected_constructor_names:
        raise VariablePythonTypeUnexpectedValue( variable_python_type)
    # must be good!
    return True

def save(types, db_url=None, connection_func=None):
    """
    persists a list of one (or more) Python types, to the warehouse database

    Keyword Parameters:
    types  --  list of Python types
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    VariablePythonTypeTypeError -- raised when variable_python_type is not a
      String
    VariablePythonTypeUnexpectedValue -- raised when variable_python_type is
      malformed

    >>> empty_list = []
    >>> save( [])
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # write out the types -- first, prepare a statement
    template = 'INSERT into {schema}.{table} (constructor_name) values (%s);'
    insert_statement = template.format(schema=dto_util.SCHEMA, table=TABLE)
    # next compose a one list of values, for each row to be inserted
    collection_of_lists = [ [t] for t in types]
    # insert! -- directly use tables dictionaries for binds
    dto_util.exec_base(collection_of_lists, validate, insert_statement, db_url=db_url
                       ,connection_func=connection_func)
