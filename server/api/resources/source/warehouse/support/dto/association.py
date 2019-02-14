"""
Module, providing a DAO api to access metadata on assocations between DW tables

Copyright (C) 2016 ERT Inc.
"""
from api.resources.source.warehouse.support import dto_util
from api.resources.source.warehouse.support.dto import table, association_type

TABLE = "table_relation"
# support table, containing catalogue of relationships between warehouse table

class ValidateTypeError(TypeError):
    """
    Exception raised when the type of a Warehouse association is not a
     dictionary.
    """
    pass
class ValidateMissingValue(ValueError):
    """
    Raised when a required, warehouse association attribute is absent.
    """
    pass
class ValidateUnexpectedValue(ValueError):
    """
    Raised when an unrecognized, warehouse Association attribute is encountered
    """
    pass

def validate( association):
    """
    validates if referenced object conforms to this module's api for table
    associations.
    
    Keyword Parameters:
    assocation  --  dictionary, representing a warehouse table association.

    Exceptions:
    ValidateTypeError -- raised when association parameter is not a dictionary
    ValidateMissingValue -- raised when association parameter is incomplete
    ValidateUnexpectedValue -- raised when association parameter is malformed

    >>> from copy import deepcopy
    >>> assoc1 = {'parent': 'depth_dim', 'parent_column': 'depth_whid', \
        'table': 'catch_fact', 'column': 'depth_whid', 'type':'fact dimension'}
    >>> validate( assoc1)
    True
    >>> validate( 'NotADict')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.association.ValidateTypeError: <class 'str'>
    >>> missing = deepcopy( assoc1); removed = missing.pop('parent')
    >>> validate( missing)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.association.ValidateMissingValue: parent
    >>> extra = deepcopy( assoc1); extra['Foo'] = 'anything'
    >>> validate( extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.association.ValidateUnexpectedValue: Foo
    """
    if not isinstance( association, dict):
        raise ValidateTypeError( type(association) )
    # verify object structure
    expected_keys = ['parent','parent_column','table','column','type']
    for key in expected_keys: #check that *all* attributes are present
        if key not in association.keys():
            raise ValidateMissingValue( key)
    for key in association.keys(): #check for any non-standard attributes
        if key not in expected_keys:
            raise ValidateUnexpectedValue( key)
    # otherwise, must be Ok!
    return True

def get_all( db_url=None, connection_func=None):
    """
    Utility function,returning association dictionaries for all table relations

    Keyword Parameters:
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArguments  -- raised if neither connection or db_url
      parameter is specified.

    >>> get_all()
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection( db_url, connection_func)
    # prepare statement, to get association metadata
    select_statement = (
        'SELECT \n'
        '   t_par.name AS parent \n'
        '  ,a.parent_table_col AS parent_column \n'
        '  ,t.name AS table \n'
        '  ,a.table_col AS column \n'
        '  ,at.type_name AS type \n'
        'FROM {schema}.{association_table} a \n'
        '  INNER JOIN {schema}.{association_type_table} at \n'
        '    ON a.table_relation_type_id = at.table_relation_type_id \n'
        '  INNER JOIN {schema}.{table_table} t \n'
        '    ON a.table_id = t.table_id \n'
        '  INNER JOIN {schema}.{table_table} t_par \n'
        '    ON a.parent_table_id = t_par.table_id \n'
        ).format( schema=dto_util.SCHEMA, association_table=TABLE
                , table_table=table.TABLE
                , association_type_table=association_type.TABLE)
    try:
        result = connection.execute( select_statement)
        associations = []
        for row in result:
            table_association = dict(zip(row.keys(),row.values()))
            validate( table_association)
            associations.append( table_association)
        return associations
    except:
        raise
    finally:
        connection.close()

def delete( associations, db_url=None, connection_func=None):
    """
    removes a list of one (or more) table associations, from the warehouse db

    Keyword Parameters:
    associations  --  list of associations
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
    # prepare statement, to remove table relation metadata
    delete_statement = (
        'DELETE FROM {schema}.{association_table} \n'
        'WHERE \n'
        '      table_id = (SELECT table_id \n'
        '                  FROM {schema}.{table_table} \n'
        '                  WHERE name=%(table)s ) \n'
        '  AND table_col = %(column)s \n'
        '  AND parent_table_id = (SELECT table_id \n'
        '                         FROM {schema}.{table_table} \n'
        '                         WHERE name=%(parent)s ) \n'
        '  AND parent_table_col = %(parent_column)s \n'
        '  AND table_relation_type_id = (SELECT table_relation_type_id \n'
        '                                FROM {schema}.{association_type_table} \n'
        '                                WHERE type_name=%(type)s ) \n'
        ).format( schema=dto_util.SCHEMA, association_table=TABLE
                , table_table=table.TABLE
                , association_type_table=association_type.TABLE)
    # delete! -- directly use associations dictionaries for binds
    dto_util.exec_base( associations, validate, delete_statement, db_url=db_url
                       ,connection_func=connection_func)

def update_by_table_column(table_name, column_name, association, db_url=None
                           ,connection_func=None):
    """
    updates one association,referenced by the table & its lookup field

    Keyword Parameters:
    table_name  -- String, representing the name of the association
      Table
    column_name  -- String, representing name of table_name's
      association Column
    association  -- DWSupport association Data Transfer Object defining
      the new association values (may *change* table_name+column_name)
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> import datetime
    >>> assoc1 = {'parent': 'depth_dim', 'parent_column': 'depth_whid', \
        'table': 'catch_fact', 'column': 'depth_whid', 'type':'fact dimension'}
    >>> update_by_table_column('any_table', 'any_column', assoc1)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # prepare statement, to update the table metadata
    update_statement = (
        'UPDATE {schema}.{association_table} SET \n'
        '   table_id = (SELECT table_id --use name of relevant key \n'
        '               FROM {schema}.{table_table} \n'
        '               WHERE name=%(table)s ) \n'
        '  ,table_col = %(column)s \n'
        '  ,parent_table_id = (SELECT table_id \n'
        '                      FROM {schema}.{table_table} \n'
        '                      WHERE name=%(parent)s ) \n'
        '  ,parent_table_col = %(parent_column)s\n'
        '  ,table_relation_type_id = (SELECT table_relation_type_id \n'
        '                             FROM {schema}.{association_type_table} \n'
        '                             WHERE type_name=%(type)s ) \n'
        '  ,aud_beg_dtm = current_timestamp \n'
        'WHERE \n'
        '  table_id = (SELECT table_id --use name of relevant key \n'
        '               FROM {schema}.{table_table} \n'
        '               WHERE name=%(arg_table_name)s ) \n'
        '  AND table_col = %(arg_column_name)s \n'
        ).format( schema=dto_util.SCHEMA, association_table=TABLE
                , table_table=table.TABLE
                , association_type_table=association_type.TABLE)
    # update! -- directly use association dictionarie for binds
    dto_util.exec_base([association], validate, update_statement, db_url=db_url
                       ,connection_func=connection_func
                       ,additional_binds={'arg_table_name': table_name
                                          ,'arg_column_name': column_name})

def save(associations, db_url=None, connection_func=None):
    """
    persists a list of one (or more) table associations, to the warehouse db

    Keyword Parameters:
    associations  --  list of associations
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
    # prepare statement, to write out the table metadata
    insert_statement = (
        'INSERT into {schema}.{association_table} ( \n'
        '   table_id \n'
        '  ,table_col \n'
        '  ,parent_table_id \n'
        '  ,parent_table_col \n'
        '  ,table_relation_type_id \n'
        ') values ( \n'
        '   (SELECT table_id \n'
        '      FROM {schema}.{table_table} \n'
        '      WHERE name=%(table)s ) --use association object key names,as the value bind targets \n'
        '  ,%(column)s --again, use name of relevant key \n'
        '  ,(SELECT table_id \n'
        '      FROM {schema}.{table_table} \n'
        '      WHERE name=%(parent)s ) \n'
        '  ,%(parent_column)s \n'
        '  ,(SELECT table_relation_type_id \n'
        '      FROM {schema}.{association_type_table} \n'
        '      WHERE type_name=%(type)s ) \n'
        ')'
        ).format( schema=dto_util.SCHEMA, association_table=TABLE
                , table_table=table.TABLE
                , association_type_table=association_type.TABLE)
    # insert! -- directly use associations dictionaries for binds
    dto_util.exec_base( associations, validate, insert_statement, db_url=db_url
                       ,connection_func=connection_func)
