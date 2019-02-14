# pylint: disable=attribute-defined-outside-init
"""
Module, implementing DAO api to access predefined queries for Variables

Warehouse tables may have None, one ("core"), two ("core/expanded"), or
more sets of selection fields predefined as a Query.

Copyright (C) 2016 ERT Inc.
"""
from collections import namedtuple

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .. import dto_util
from . import (association, association_type, table, table_type, variable)

TABLE = 'query'
#string,representing the DWSupport schema table that holds Query records

QUERY_VARIABLE_TABLE = 'query_variable'
#string,representing DWSupport schema table holding Query variable records

class UnexpectedValue(ValueError):
    """
    Query has unrecognized attribute
    """
    pass

class MissingValue(ValueError):
    """
    Query has a missing attribute
    """
    pass

class ValueTypeError(TypeError):
    """
    Query attribute is of an unexpected type
    """
    pass

def validate(query):
    """
    Returns True if referenced object conforms module's Query api

    Keyword Parameters:
    query  -- Dict, representing a warehouse Query

    Exceptions:
    MissingValue -- raised when a query Data Transfer Object (dto) is
      incomplete
    UnexpectedValue -- raised when a dto fails validation, due to extra
      attributes
    ValueTypeError -- raised when a dto attribute is of an unexpected
      type

    >>> query_simple = {'table': 'foo_table', 'name': 'core', 'variables': {}}
    >>> validate(query_simple)
    True
    >>> query_missing = {'table': 'foo_table', 'name': 'example'}
    >>> validate(query_missing)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.query.MissingValue: {'variables'}
    >>> query_extra = dict(query_simple)
    >>> query_extra['not_expected'] = "Anything"
    >>> validate(query_extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.query.UnexpectedValue: {'not_expected'}
    """
    expected_keys = {'table', 'name', 'variables'}
    extra_keys = query.keys() - expected_keys
    if any(extra_keys):
        raise UnexpectedValue(extra_keys)
    missing_keys = expected_keys - query.keys()
    if any(missing_keys):
        raise MissingValue(missing_keys)
    # check if variables attribute is Dict-like
    try:
        query['variables'].keys()
    except AttributeError as e:
        raise ValueTypeError('variables') from e
    return True

def _get_declarative_model_and_bind_class(connection):
    """
    returns DB declarative_model & a Class mapped to dwsupport.query

    Keyword Parameters:
    connection  -- an open SQLAlchemy connection object
    """
    # Configure a Python class mapping for the DB table
    engine = connection.engine
    declarative_model = declarative_base(engine)

    class Query(declarative_model):
        """
        class representing a row from dwsupport.query
        """
        __tablename__ = TABLE
        __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}

    class QueryVariable(declarative_model):
        """
        class representing a row from dwsupport.query
        """
        __tablename__ = QUERY_VARIABLE_TABLE
        __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}

    return declarative_model, Query, QueryVariable

def get_all(db_url=None, connection_func=None):
    """
    returns list of all Queries persisted to the DB

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
        declarative_model, Query, QueryVariable = model_class_tuple

        # Retreive Autoloaded structure
        db_structure = declarative_model.metadata

        # Fully-qualify (schema.table_name) names of tables needed for saving
        schema_base = dto_util.SCHEMA + '.'

        table_table = db_structure.tables[schema_base+table.TABLE]
        query_variable_table_table = table_table.alias('table_query_variable')
        variable_table = db_structure.tables[schema_base+variable.TABLE]

        query_variable_on_clause = (
            QueryVariable.variable_id == variable_table.c.variable_id
        )
        query_variable_table_on_clause = (
            QueryVariable.table_id == query_variable_table_table.c.table_id
        )

        # open connection
        session = Session(connection)

        # get Query objects
        queries_query = session.query(Query).\
            join(table_table).\
            join(QueryVariable, QueryVariable.query_id == Query.query_id).\
            join(variable_table, query_variable_on_clause).\
            join(query_variable_table_table, query_variable_table_on_clause).\
            add_columns(
                 table_table.c.name
                ,Query.name.label('test')
                ,variable_table.c.column_name
                ,query_variable_table_table.c.name.label('variable_table')
            )

        # convert SQL result into minimal Query Dict
        queries_by_table_name_tuple = dict()
        for result in queries_query.all():
            table_name = result.name
            query_name = result.test #TODO: change
            key = (table_name, query_name)
            initial_query = {'table': table_name, 'name': query_name
                             ,'variables': dict()} #New, empty dict
            query = queries_by_table_name_tuple.setdefault(key, initial_query)
            variables_key = result.variable_table
            column_list = query['variables'].setdefault(variables_key, [])
            column_list.append(result.column_name)
            queries_by_table_name_tuple[key] = query

        return list(queries_by_table_name_tuple.values())

def save(queries, db_url=None, connection_func=None):
    """
    persists a list of one or more Queries to the DB

    Keyword Parameters:
    queries  -- list of warehouse Queries
    db_url  -- String, representing a SQLAlchemy connection(Required, if
      parameter 'connection' is not provided.
    connection_func  --function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    MissingValue -- raised when a Query Data Transfer Object (dto) is
      incomplete
    UnexpectedValue -- raised when a dto fails validation, due to extra
      attributes
    """
    for query in queries:
        validate(query)

    # push items to the DB
    with dto_util.get_connection(db_url, connection_func) as connection:
        # Discover db structure & map the custom ID table signature to a class
        model_class_tuple = _get_declarative_model_and_bind_class(connection)
        declarative_model, Query, QueryVariable = model_class_tuple

        class Association(declarative_model):
            """
            class representing a row from dwsupport.table_relation
            """
            __tablename__ = association.TABLE
            __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}

        class AssociationType(declarative_model):
            """
            class representing a row from dwsupport.table_relation_type
            """
            __tablename__ = association_type.TABLE
            __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}

        # Retreive Autoloaded structure
        db_structure = declarative_model.metadata

        # Fully-qualify (schema.table_name) names of tables needed for saving
        schema_base = dto_util.SCHEMA + '.'

        table_table = db_structure.tables[schema_base+table.TABLE]
        table_type_table = db_structure.tables[schema_base+table_type.TABLE]
        variable_table = db_structure.tables[schema_base+variable.TABLE]

        # open connection
        session = Session(connection)

        # convert friendly API dicts, into SQL binds
        for query in queries:
            # build new Query object, to save to DB
            insert_query = Query()
            # lookup the Query's table primary-key, by table's name/project
            table_name = query['table']
            table_rows_query = session.query(table_table).\
                filter(table_table.c.name == table_name)
            table_row = table_rows_query.one()
            insert_query.table_id = table_row.table_id
            insert_query.name = query['name']
            session.add(insert_query)
            session.flush() #get a query_id for the newly added Query

            # build new query_varible objects, from the variables Dict
            query_variable_insert_objects = list()
            for table_name, column_names in query['variables'].items():
                # look up the QueryVariable's table primary-key
                table_rows_query = session.query(table_table).\
                    join(table_type_table).\
                    filter(table_table.c.name == table_name).\
                    add_columns(table_type_table.c.type_name)
                table_row = table_rows_query.one()
                #a Query variable may have multiple columns, for a single source subtable
                for column_name in column_names:
                    insert_query_variable = QueryVariable(
                         query_id = insert_query.query_id
                        ,table_id = table_row.table_id
                    )
                    variable_table_id=table_row.table_id
                    if table_row.type_name in ['dimension role']:
                        #Table is a Role alias for another table;find base table_id
                        association_query = session.query(Association).\
                            filter(Association.table_id == table_row.table_id).\
                            join(AssociationType).\
                            filter(AssociationType.type_name == 'dimension role base')
                        association_row = association_query.one()
                        variable_table_id = association_row.parent_table_id
                    # look up the QueryVariable's variable primary-key, by variable name
                    variable_name = column_name
                    variable_rows_query = session.query(variable_table).\
                        filter(variable_table.c.column_name == variable_name).\
                        filter(variable_table.c.table_id == variable_table_id)
                    variable_row = variable_rows_query.one()
                    insert_query_variable.variable_id = variable_row.variable_id
                    query_variable_insert_objects.append(insert_query_variable)
            session.bulk_save_objects(query_variable_insert_objects)

        # save
        session.commit()

def update_by_table_and_name(table_name, query_name, new_query, db_url=None, connection_func=None):
    """
    Modifies contents of a single persisted DWSupport query.

    Returns the new Query object

    Keyword Parameters:
    table_name  -- String, representing Query to update's current table.
    query_name  -- String, representing current name of the Query to
      update.
    new_query  -- Query Data Transfer Object (DTO) containing the new
      values.
    db_url  -- String, representing a SQLAlchemy connection(Required, if
      parameter 'connection' is not provided.
    connection_func  --function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    MissingValue -- raised when new_query is incomplete.
    UnexpectedValue -- raised when new_query fails validation, due to extra
      attributes
    """
    validate(new_query)

    # push update to the DB
    with dto_util.get_connection(db_url, connection_func) as connection:
        # Discover db structure & map the custom ID table signature to a class
        model_class_tuple = _get_declarative_model_and_bind_class(connection)
        declarative_model, Query, QueryVariable = model_class_tuple

        class Association(declarative_model):
            """
            class representing a row from dwsupport.table_relation
            """
            __tablename__ = association.TABLE
            __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}

        class AssociationType(declarative_model):
            """
            class representing a row from dwsupport.table_relation_type
            """
            __tablename__ = association_type.TABLE
            __table_args__ = {'autoload': True, 'schema': dto_util.SCHEMA}

        # Retreive Autoloaded structure
        db_structure = declarative_model.metadata

        # Fully-qualify (schema.table_name) names of tables needed to save
        schema_base = dto_util.SCHEMA + '.'

        table_table = db_structure.tables[schema_base+table.TABLE]
        table_type_table = db_structure.tables[schema_base+table_type.TABLE]
        variable_table = db_structure.tables[schema_base+variable.TABLE]

        # open connection
        session = Session(connection)

        # update db
        # lookup the Query's table primary-key, by table's name/project
        query_query = session.query(Query).\
            join(table_table).\
            filter(table_table.c.name == table_name).\
            filter(Query.name == query_name)
        query_row = query_query.one()
        # set new name
        query_row.name = new_query['name']
        # set new table
        new_table_query = session.query(table_table).\
            filter(table_table.c.name == new_query['table'])
        new_table_row = new_table_query.one()
        query_row.table_id = new_table_row.table_id

        current_query_variables_query = session.query(QueryVariable).\
            join(table_table, QueryVariable.table_id == table_table.c.table_id).\
            join(variable_table, QueryVariable.variable_id == variable_table.c.variable_id).\
            filter(QueryVariable.query_id == query_row.query_id).\
            add_columns( table_table.c.name.label('table_name')
                        ,variable_table.c.column_name
                        ,QueryVariable.query_id
                        ,QueryVariable.table_id
                        ,QueryVariable.variable_id)
        current_query_variables = current_query_variables_query.all()
        #build a dictionary of all current table+columns, for fast reference
        current_map = {(qv.table_name, qv.column_name): qv #map by table+column
                       for qv #a current Query variable
                       in current_query_variables}
        # update variables
        new_variables = new_query['variables']
        # save new variables
        # determine which query variables need to be added
        new_variable_names_by_table_name = _vars_to_add(new_variables, current_map)
        all_new_variable_names = []
        for new_variables_for_table in new_variable_names_by_table_name.values():
            all_new_variable_names.extend(new_variables_for_table)
        # retrieve Table_ids, and variable_ids for the new query variables
        new_table_and_variable_ids_query = session.query(table_table).\
            outerjoin(variable_table, full=True).\
            filter(table_table.c.name.in_(new_variable_names_by_table_name.keys())
                    | #OR
                    variable_table.c.column_name.in_(all_new_variable_names)
            ).add_columns(variable_table.c.variable_id, variable_table.c.column_name)
        new_table_and_variable_ids = new_table_and_variable_ids_query.all()
        # insert new query_variables
        new_query_variables = [QueryVariable( query_id=query_row.query_id
                                             ,table_id=qv_new_var.table_id
                                             ,variable_id=qv_new_var.variable_id)
                               for qv_new_var
                               in _new_vars( new_variable_names_by_table_name
                                            ,new_table_and_variable_ids)]
        session.bulk_save_objects(new_query_variables)
        # remove deleted variables
        # compose a list of every table+column_name QueryVariable which is to be kept
        new_variables_keys = set()
        for variable_table, variable_names in new_variables.items():
            for variable_name in variable_names:
                key = (variable_table, variable_name)
                new_variables_keys.add(key)
        # delete any QueryVariable found in the db that isnt on the list
        for persisted_query_variable in current_query_variables:
            key = (persisted_query_variable.table_name, persisted_query_variable.column_name)
            if key not in new_variables_keys:
                query_variable_query = session.query(QueryVariable).\
                    filter(QueryVariable.query_id==persisted_query_variable.query_id).\
                    filter(QueryVariable.table_id==persisted_query_variable.table_id).\
                    filter(QueryVariable.variable_id==persisted_query_variable.variable_id)
                query_variable = query_variable_query.one()
                session.delete(query_variable)
        #save
        session.commit()
    return new_query

def _vars_to_add(new_query_variables, current_query_variables):
    """
    Return list of dicts representing Query Variables not yet persisted

    Keyword Parameters:
    new_query_variables  -- Dict, representing a new inventory of Query
      Variables, to be associated with a DWSupport Query
    current_query_variables  -- Dict, representing the Query Variables
      currently associated with the 'new_query_variables' Query mapped
      by tuple(table_name, column_name)

    >>> from pprint import pprint
    >>> test_new_vars = { 'great_fact': ['measure_a', 'measure_b']
    ...                   ,'useful_dim': ['field_one']
    ...                   ,'occasionally_useful_dim': ['field_two']}
    >>> persisted_vars = { ('great_fact', 'measure_a'): object() #fake
    ...                   ,('useful_dim', 'field_one'): object()#objects
    ...                   ,('useful_dim', 'field_two'): object()}
    >>> out = _vars_to_add(test_new_vars, persisted_vars)
    >>> pprint(out) # check detected additions
    {'great_fact': ['measure_b'], 'occasionally_useful_dim': ['field_two']}
    """
    additional_fields_by_table_name = {} # Values to return
    # detect additions
    for new_variable_table_name, table_columns in new_query_variables.items():
        for column_name in table_columns:
            key = (new_variable_table_name, column_name) #table+column tuple
            if key not in current_query_variables:
                # New Query Variable - add variable name to table's list
                table_variables = additional_fields_by_table_name.setdefault(
                     new_variable_table_name
                    ,list()) #default to new, empty list (if none exists yet)
                table_variables.append(column_name)
    return additional_fields_by_table_name

def _new_vars(new_variable_names_by_table_name, new_table_and_variable_ids):
    """
    Return dictionaries representing QueryVariable args, to save to db

    Keyword Parameters:
    new_variable_names_by_table_name  -- dict, representing the new
      QueryVariables to be saved.
    new_table_and_variable_ids  -- SQLAlchemy resultset containing union
      of all Table names+table_ids and Variable IDs+column_names for the
      new QueryVariables

    >>> from pprint import pprint, pformat
    >>> FakeRow = namedtuple('FakeRow', [ 'name', 'table_id', 'column_name'
    ...                                      ,'variable_id'])
    >>> new_ids = [ FakeRow( name='great_fact', table_id=1
    ...                     ,column_name='measure_a', variable_id=1)
    ...            ,FakeRow( name='great_fact', table_id=1
    ...                     ,column_name='measure_b', variable_id=2)
    ...            ,FakeRow( name='occasionally_useful_dim', table_id=3
    ...                     ,column_name='field_one', variable_id=3)
    ...            ,FakeRow( name='occasionally_useful_dim', table_id=3
    ...                     ,column_name='field_two', variable_id=4)]
    >>> new_query_variables = { 'great_fact': ['measure_b']
    ...                        ,'occasionally_useful_dim': ['field_two']}
    >>> out = _new_vars(new_query_variables, new_ids)
    >>> out.sort(key=pformat) # stabilize sort order, for testing
    >>> pprint(out) # check QueryVariable argument pairs
    [QueryVariableArgs(table_id=1, variable_id=2),
     QueryVariableArgs(table_id=3, variable_id=4)]
    """
    # define named tuple, with same constructor as the SQLAlchemy mapped class
    #  for dwsupport.query_variable
    QueryVariableArgs = namedtuple('QueryVariableArgs', ['table_id', 'variable_id'])
    # make maps for fast lookup: table_id by name, variable_id by column name
    table_ids_by_name = {}
    variable_ids_by_column_name = {}
    for row in new_table_and_variable_ids:
        table_ids_by_name.setdefault(row.name, row.table_id)
        variable_ids_by_column_name.setdefault(row.column_name, row.variable_id)
    # produce the list of QueryVariable arguments, for new table+variable pairs
    arguments = []
    for table_name, variable_names in new_variable_names_by_table_name.items():
        for variable_name in variable_names:
            table_id = table_ids_by_name[table_name]
            variable_id = variable_ids_by_column_name[variable_name]
            sql_args = QueryVariableArgs( table_id=table_id
                                         ,variable_id=variable_id)
            arguments.append(sql_args)
    return arguments
