"""
Module, implementing DAO api to access custom IDs for warehouse Variables

Variables are the fields (measured values & dimensional attributes) contained
within the warehouse. Custom IDs are the admin-provided names used to
refer to the Variable via the web API.

Copyright (C) 2016 ERT Inc.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .. import dto_util
from . import (table, table_type, association, association_type, variable)

TABLE = 'variable_custom_identifier'

class UnexpectedValue(ValueError):
    """
    Variable Custom Identifier has unrecognized attribute
    """
    pass
    
class MissingValue(ValueError):
    """
    Variable Custom Identifier has a missing attribute
    """
    pass
    
def validate(variable_custom_identifier):
    """
    Returns True if referenced object conforms module's custom ID api
    
    Keyword Parameters:
    variable_custom_identifier  -- Dict, representing a warehouse
      Variable custom ID.

    Exceptions:
    MissingValue -- raised when a Variable custom ID Data Transfer
      Object (dto) is incomplete.
    UnexpectedValue -- raised when a dto fails validation, due to extra
      attributes
      
    >>> custom_simple = {'table': 'foo_table', 'column': 'bar_ml', 'id': 'bar'}
    >>> validate(custom_simple)
    True
    >>> custom_missing = { 'table': 'foo_table', 'column': 'bar_ml'}
    >>> validate(custom_missing)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.variable_custom_identifier.MissingValue: {'id'}
    >>> custom_extra = dict(custom_simple)
    >>> custom_extra['not_expected'] = "Anything"
    >>> validate(custom_extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.variable_custom_identifier.UnexpectedValue: {'not_expected'}
    """
    expected_keys = {'table', 'column', 'id'}
    extra_keys = variable_custom_identifier.keys() - expected_keys
    if any(extra_keys):
        raise UnexpectedValue(extra_keys)
    missing_keys = expected_keys - variable_custom_identifier.keys()
    if any(missing_keys):
        raise MissingValue(missing_keys)
    return True

def _get_declarative_model_and_bind_class(connection):
    """
    returns DB declarative_model & a Class mapped to variable_custom_identifier
    
    Keyword Parameters:
    connection  -- an open SQLAlchemy connection object
    """
    # Configure a Python class mapping for the DB table
    engine = connection.engine
    declarative_model = declarative_base(engine)
    
    class VariableCustomIdentifier(declarative_model):
        """
        class representing a row from dwsupport.variable_custom_identifier
        """
        __tablename__ = TABLE
        __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}

    class Association(declarative_model):
        """
        class representing a row from dwsupport.variable_custom_identifier
        """
        __tablename__ = association.TABLE
        __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}
        
    return declarative_model, VariableCustomIdentifier, Association

def get_all(db_url=None, connection_func=None):
    """
    returns list of all Variable custom IDs persisted to the DB

    Keyword Parameters:
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    """
    # pull items from the DB
    with dto_util.get_connection(db_url, connection_func) as connection:
        # Discover db structure & map the custom ID table signature to a class
        model_class_tuple = _get_declarative_model_and_bind_class(connection)
        declarative_model, VariableCustomIdentifier = model_class_tuple[:2]

        # Retreive Autoloaded structure
        db_structure = declarative_model.metadata

        # Fully-qualify (schema.table_name) names of tables needed for saving
        schema_base = dto_util.SCHEMA + '.'

        table_table = db_structure.tables[schema_base+table.TABLE]
        variable_table = db_structure.tables[schema_base+variable.TABLE]

        # open connection
        session = Session(connection)
        
        # get objects
        onclause_variable_table = (
            VariableCustomIdentifier.variable_id == variable_table.c.variable_id
        )
        custom_ids_query = session.query(VariableCustomIdentifier).\
            join(table_table).\
            join(variable_table, onclause_variable_table).\
            add_columns(
                 table_table.c.name
                ,variable_table.c.column_name
                ,VariableCustomIdentifier.custom_identifier
            )

        # convert SQL result into variable_custom_identifier Dict
        variable_custom_identifiers = list()
        for result in custom_ids_query.all():
            custom_id = dict()
            custom_id['table'] = result.name
            custom_id['column'] = result.column_name
            custom_id['id'] = result.custom_identifier
            variable_custom_identifiers.append(custom_id)

        return variable_custom_identifiers
    
def save(variable_custom_identifiers, db_url=None, connection_func=None):
    """
    persists a list of one or more Variable custom IDs to the DB

    Keyword Parameters:
    variable_custom_identifiers  -- list of Variable custom IDs
    db_url  -- String, representing a SQLAlchemy connection(Required, if
      parameter 'connection' is not provided.
    connection_func  --function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    MissingValue -- raised when a Variable custom ID Data Transfer
      Object (dto) is incomplete.
    UnexpectedValue -- raised when a dto fails validation, due to extra
      attributes
    """
    for custom_id in variable_custom_identifiers:
        validate(custom_id)

    # push items to the DB
    with dto_util.get_connection(db_url, connection_func) as connection:
        # Discover db structure & map the custom ID table signature to a class
        model_class_tuple = _get_declarative_model_and_bind_class(connection)
        declarative_model, VariableCustomIdentifier = model_class_tuple[:2]

        # Retreive Autoloaded structure
        db_structure = declarative_model.metadata

        # Fully-qualify (schema.table_name) names of tables needed for saving
        schema_base = dto_util.SCHEMA + '.'

        table_table = db_structure.tables[schema_base+table.TABLE]
        table_type_table = db_structure.tables[schema_base+table_type.TABLE]
        association_table = db_structure.tables[schema_base+association.TABLE]
        association_type_table = db_structure.tables[schema_base+association_type.TABLE]
        variable_table = db_structure.tables[schema_base+variable.TABLE]

        # open connection
        session = Session(connection)

        # convert friendly API dicts, into SQL binds
        sql_insert_objects = list()
        for custom_id in variable_custom_identifiers:
            # build new dictionary, to save to DB
            insert_binds = dict()
            # lookup Custom ID's table primary-key & type, by table's name/project
            table_name = custom_id['table']
            table_rows_query = session.query(table_table).\
                join(table_type_table).\
                filter(table_table.c.name == table_name).\
                add_columns(table_type_table.c.type_name)
            table_row = table_rows_query.one()
            insert_binds['table_id'] = table_row.table_id
            custom_id_base_table_name = custom_id['table']
            if table_row.type_name == 'dimension role':
                #The target variable record doesnt have the same table name
                #all variable records are stored against the dimension Base
                base_table_table = table_table.alias('table_base')
                base_table_query = session.query(base_table_table).\
                    join(association_table, base_table_table.c.table_id == association_table.c.parent_table_id).\
                    join(table_table, table_table.c.table_id == association_table.c.table_id).\
                    join(association_type_table).\
                    filter(association_type_table.c.type_name == 'dimension role base').\
                    filter(table_table.c.name == custom_id['table'])
                base_table_row = base_table_query.one()
                custom_id_base_table_name = base_table_row.name
            # look up the Custom ID's variable primary-key, by variable name
            variable_name = custom_id['column']
            variable_rows_query = session.query(variable_table).\
                join(table_table).\
                filter(variable_table.c.column_name == variable_name).\
                filter(table_table.c.name == custom_id_base_table_name)
            variable_row = variable_rows_query.one()
            insert_binds['variable_id'] = variable_row.variable_id
            # specify custom ID
            insert_binds['custom_identifier'] = custom_id['id']
            insert_object = VariableCustomIdentifier(**insert_binds)
            sql_insert_objects.append(insert_object)
            
        # save
        session.bulk_save_objects(sql_insert_objects)
        session.commit()
