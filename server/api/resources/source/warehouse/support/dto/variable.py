"""
Module, providing a DAO api for accessing metadata on warehoused Variables.

Variables are the fields (measured values & dimensional attributes) contained
within the warehouse. Variable metadata describes the how to access and use a
fields contents.

Copyright (C) 2016 ERT Inc.
"""
from api.resources.source.warehouse.support import dto_util
from api.resources.source.warehouse.support.dto import (
                                                         table
                                                        ,variable_python_type
                                                       )
import logging

TABLE = "variable"
# support table,containing the list of variables which compose the warehouse

class VariableTypeError(TypeError):
    """
    Exception raised when the type of a Warehouse metadata variable is not a
     dictionary.
    """
    pass
class VariableMissingValue(ValueError):
    """
    Raised when a required, warehouse metadata Variable attribute is absent.
    """
    pass
class VariableUnexpectedValue(ValueError):
    """
    Raised when an unrecognized, warehouse Variable attribute is encountered.
    """
    pass

def validate( variable):
    """
    validate if referenced object conforms to this module's api for warehouse
    variable metadata.

    Keyword Parameters:
    variable -- dictionary representing a warehoused variable(i.e.: data field)

    Exceptions:
    VariableTypeError -- raised when variable parameter is not a dictionary
    VariableMissingValue -- raised when variable parameter is incomplete
    VariableUnexpectedValue -- raised when variable parameter is malformed

    >>> from copy import deepcopy
    >>> var1 = { 'column':'frob_hz', 'title':'Frobniz Resonance (Hz)'
    ...         ,'python_type': 'float', 'physical_type': 'numeric'
    ...         ,'table': 'foo_fact', 'max_length': 147456
    ...         ,'units': 'hertz', 'precision': 16383
    ...         ,'description': 'A useful value!'
    ...         ,'allowed_values': '1+e-16383 - 9e147456'}
    >>> validate( var1)
    True
    >>> validate( '{"column":"json_variable"}')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.variable.VariableTypeError: <class 'str'>
    >>> partial = deepcopy(var1); removed = partial.pop('python_type')
    >>> validate( partial)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.variable.VariableMissingValue: python_type
    >>> extra = deepcopy(var1); extra['shouldnt_be_here!'] = True
    >>> validate( extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.variable.VariableUnexpectedValue: shouldnt_be_here!
    """
    # verify object type
    if not isinstance( variable, dict):
        raise VariableTypeError( type(variable))
    # verify object contents
    expected_keys = ['column','table','title','python_type', 'physical_type'
                     ,'units', 'max_length', 'precision', 'allowed_values'
                     ,'description']
    for key in expected_keys: #check that *all* attributes are present
        if key not in variable.keys():
            raise VariableMissingValue( key)
    for key in variable.keys(): #check for any non-standard attributes
        if key not in expected_keys:
            raise VariableUnexpectedValue( key)
    # must be good!
    return True

def get(table_name=None, db_url=None, connection_func=None):
    """
    retrive the current list of variables from the warehouse support schema.
    (Optionally filtered to just 1x table)

    Keyword Parameters:
    table  -- String, representing the name of a Warehoused table
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArgument  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> get()
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection( db_url, connection_func)
    # prepare statement, to get variable metadata
    select_statement = (
        'SELECT \n'
        '   v.column_name AS column \n'
        '  ,v.title \n'
        '  ,v.description \n'
        '  ,t.name AS table\n'
        '  ,pt.constructor_name AS python_type \n'
        '  ,v.column_type AS physical_type \n'
        '  ,v.units \n'
        '  ,v.max_length \n'
        '  ,v.precision \n'
        '  ,v.allowed_values \n'
        'FROM {schema}.{variable_table} v \n'
        '  INNER JOIN {schema}.{python_type_table} pt \n'
        '    ON v.variable_python_type_id = pt.variable_python_type_id \n'
        '  INNER JOIN {schema}.{table_table} t \n'
        '    ON v.table_id = t.table_id \n'
        'WHERE \n'
        '  (CASE WHEN %(name)s IS NOT NULL AND t.name = %(name)s \n'
        '      THEN 1 --if name specified, return row only if name matches \n'
        '    WHEN %(name)s IS NULL \n'
        '      THEN 1 --if no name specified,return all variables(i.e.: 1=1)\n'
        '    ELSE 0 --dont return row if name specified but doesnt match row\n'
        '   END) = 1 \n'
        ).format( schema=dto_util.SCHEMA, variable_table=TABLE
                , table_table=table.TABLE
                , python_type_table=variable_python_type.TABLE)
    try:
        result = connection.execute( select_statement, name=table_name)
        variables = []
        for row in result:
            variable = dict(row)
            validate(variable)
            variables.append(variable)
        return variables
    except:
        raise
    finally:
        connection.close()

def get_by_lookup(table_names, db_url=None, connection_func=None):
    """
    Utility function,returning variable dictionaries associated with named tables.

    Keyword Parameters:
    table_names  --  A collection of table names, for which the table
      variables are to be retrieved.
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArguments  -- raised if neither connection or db_url
      parameter is specified.

    >>> any_list = ['any_thing']
    >>> get_by_lookup( any_list)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection #FIXME: connection should really just be an Engine
    discover_connection = dto_util.get_connection( db_url, connection_func)
    # retrieve fields
    select_statement = (
        'SELECT \n'
        '   DISTINCT c.table_name as table \n'
        '  ,c.column_name as column \n'
        'FROM \n'
        '  information_schema.tables t \n'
        '  INNER JOIN information_schema.columns c \n'
        '    ON t.table_schema = c.table_schema \n'
        '    AND t.table_name = c.TABLE_NAME \n'
        '  INNER JOIN pg_catalog.pg_attribute a  --Identify fields used in Foreign key lookups \n'
      '''    ON a.attrelid = (t.table_schema||'."'||t.table_name||'"')::regclass \n'''
        '    AND a.attname = c.column_name \n'
        '  left outer join pg_catalog.pg_constraint con -- match table attribute # to any lookup \n'
      '''    ON con.conrelid = (t.table_schema||'."'||t.table_name||'"')::regclass \n'''
      '''    AND con.contype = 'f' -- only FOREIGN key constraints \n'''
        '    AND a.attnum = ANY(con.conkey) \n'
        '  left outer join pg_catalog.pg_constraint con_f -- match table attribute # to any lookup \n'
      '''    ON con_f.confrelid = (t.table_schema||'."'||t.table_name||'"')::regclass \n'''
      '''    AND con_f.contype = 'f' -- only FOREIGN key constraints \n'''
        '    AND a.attnum = ANY(con_f.confkey) \n'
        'WHERE \n'
        '      t.table_name = %s \n'
        '  AND con.conkey IS Null --a result with no constraint Keys arent used in a fk lookup \n'
        '  AND con_f.confkey IS Null --a result with no constraint Keys isnt used by a fk lookup \n'
        )
    try:
        # build list of variable dicts
        variables = []
        for name in table_names:
            result = discover_connection.execute( select_statement, name)
            for row in result:
                table, column = row['table'], row['column']
                try:
                    python_type = variable_python_type.get_by_lookup( table, column
                                                    ,db_url, connection_func)
                except variable_python_type.LookupNullType as e:
                    logging.info(e, exc_info=True)
                    continue #skip this table field
                variable = {'table': table,'column': column
                            ,'title': None, 'description': None
                            ,'python_type': python_type, 'physical_type':None
                            ,'units': None, 'max_length': None
                            ,'precision': None, 'allowed_values': None}
                validate( variable)
                variables.append( variable)
        return variables
    except:
        raise
    finally:
        discover_connection.close()

def delete(variables, db_url=None, connection_func=None):
    """
    removes a list of one (or more) variables, from the warehouse db

    Keyword Parameters:
    variables  --  list of variables
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
    >>> delete( [])
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # prepare statement, to remove table variable metadata
    delete_statement = (
        'DELETE FROM {schema}.{variable_table} \n'
        'WHERE \n'
        '      table_id = (SELECT t.table_id \n'
        '                  FROM {schema}.{table_table} t \n'
        '                  WHERE t.name=%(table)s ) \n'
        '  AND column_name = %(column)s '
        ).format(schema=dto_util.SCHEMA, variable_table=TABLE
                 ,table_table=table.TABLE)
    # delete! -- directly use variables dictionaries for binds
    dto_util.exec_base( variables, validate, delete_statement, db_url=db_url
                       ,connection_func=connection_func)

def save(variables, db_url=None, connection_func=None):
    """
    persists a list of one (or more) variables, to the warehouse database

    Keyword Parameters:
    variables  --  list of variables
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
    >>> save( [])
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # prepare statement, to write out the variable metadata
    insert_statement = (
        'INSERT into {schema}.{variable_table} ( \n'
        '   column_name \n'
        '  ,title \n'
        '  ,table_id \n'
        '  ,variable_python_type_id \n'
        '  ,column_type \n'
        '  ,units \n'
        '  ,max_length \n'
        '  ,precision \n'
        '  ,allowed_values \n'
        ') values ( \n'
        '   %(column)s --use the same key name, as the variable dictionary \n'
        '  ,%(title)s --again, use name of the relevant variable key \n'
        '  ,(SELECT table_id \n'
        '      FROM {schema}.{table_table} \n'
        '      WHERE name=%(table)s  )  \n'
        '  ,(SELECT variable_python_type_id \n'
        '      FROM {schema}.{python_type_table} \n'
        '      WHERE constructor_name=%(python_type)s  )  \n'
        '  ,%(physical_type)s \n'
        '  ,%(units)s \n'
        '  ,%(max_length)s \n'
        '  ,%(precision)s \n'
        '  ,%(allowed_values)s \n'
        ') \n'
        ).format( schema=dto_util.SCHEMA, variable_table=TABLE
                , table_table=table.TABLE
                , python_type_table=variable_python_type.TABLE)
    # insert! -- directly use tables dictionaries for binds
    dto_util.exec_base(variables, validate, insert_statement, db_url=db_url
                       ,connection_func=connection_func)

def update_by_table_column(table_name, column, variable, db_url=None
                           ,connection_func=None):
    """
    updates a variable (identified by name) in the warehouse database

    Keyword Parameters:
    table_name  -- String, table which the variable to update belongs to
    column  -- String, representing the column of the variable to update
    variable  --  Dict, representing the new variable values (May change
      the table and/or column name!)
    db_url  --  String, representing a SQLAlchemy connection (Required,
      if parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url
      parameter is specified.
    ValidateException -- raised when a problem is encountered validating
      a dto

    >>> var1 = { 'column':'frob_hz', 'title':'Frobniz Resonance (Hz)'
    ...         ,'python_type': 'float', 'physical_type': 'numeric'
    ...         ,'table': 'some_table', 'max_length': 147456
    ...         ,'units': 'hertz', 'precision': 16383
    ...         ,'description': 'A useful value!'
    ...         ,'allowed_values': '1+e-16383 - 9e147456'}
    >>> update_by_table_column('some_table', 'frob_hz', var1)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # prepare statement, to update table metadata
    template = """UPDATE {schema}.{table} SET
                     column_name = %(column)s
                    ,title = %(title)s
                    ,description = %(desecription)s
                    ,table_id = (SELECT table_id
                                 FROM {schema}.{table_table}
                                 WHERE name=%(table)s )
                    ,variable_python_type_id = (
                       SELECT variable_python_type_id
                       FROM {schema}.{python_type_table}
                       WHERE constructor_name=%(python_type)s )
                    ,column_type = %(physical_type)s
                    ,units = %(units)s
                    ,max_length = %(max_length)s
                    ,precision = %(precision)s
                    ,allowed_values = %(allowed_values)s
                  WHERE column_name = %(arg_column)s
                    AND table_id = (SELECT table_id
                                    FROM {schema}.{table_table}
                                    WHERE name=%(arg_table_name)s )"""
    update_statement = template.format(schema=dto_util.SCHEMA, table=TABLE
                                       ,table_table=table.TABLE
                                       ,python_type_table=variable_python_type.TABLE
                                      )
    # update! -- directly use tables dictionary for binds
    dto_util.exec_base([variable], validate, update_statement, db_url=db_url
                       ,connection_func=connection_func
                       ,additional_binds={'arg_table_name': table_name
                                          ,'arg_column': column})
