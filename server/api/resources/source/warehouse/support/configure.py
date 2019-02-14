"""
Module providing high-level functions for configuring the DWSupport schema

Copyright (C) 2016-2017 ERT Inc.
"""
from collections import Counter

from api import json
from api.resources.source import (
     variables
)
from api.resources.source.warehouse import (
     warehouse
    ,util
)
from api.resources.source.warehouse.support import (
    discover
    ,dto
)
from api.resources.source.warehouse.support.dto_util import ConnectionMissingArgument

class WarehouseConnectionMissingArgument(ConnectionMissingArgument):
    """
    missing db params, representing location of Warehouse data tables
    """
    pass

class DWSupportConnectionMissingArgument(ConnectionMissingArgument):
    """
    missing db params, representing location of DWSupport configuration
    """
    pass

class CopyTableUnsupportedTableType(ValueError):
    """
    unable to copy this table_type
    """
    pass

class CopyTableDuplicateCopyName(ValueError):
    """
    proposed table name is not unique
    """
    pass

class CopyTableMissingVariableCustomIdentifiers(KeyError):
    """
    missing new variable custom identifiers for existing custom IDs
    """
    pass

class CopyTableNonuniqueVariableCustomIdentifiers(ValueError):
    """
    proposed variable custom identifiers are not globally unique
    """
    pass

dimension_lookup_suffix = '_whid'
"""
String, representing the convention for naming Dimensional lookup fields
"""

def add_fact(fact_name, dw_url=None, dw_connection_func=None, dwsupport_url=None
             ,dwsupport_connection_func=None):
    """
    Enroll new Fact table (& all neccessary dependant Dimensions/Roles)

    Keyword Parameters:
    fact_name  -- String, representing the name of the fact table to add
    dw_url  --  String, representing a SQLAlchemy connection to the Data
      Warehouse database (Required, if parameter 'dw_connection' is not
      provided)
    connection_func  -- function returning SQLAlchemy connections to the
      database containing Data Warehouse data assets (Optional,
      if provided, will override db_url)
    dwsupport_url  --  String, representing a SQLAlchemy connection to
      the database which contains the DWSupport warehouse model(Required
      , if parameter 'dwsupport_connection' is not provided)
    dwsupport_connection_func  -- function returning SQLAlchemy
      connections to the database containing the DWSupport configuration
      model (Optional, if provided, will override db_url)

    Exceptions:
    WarehouseConnectionMissingArgument  -- raised if neither
      dw_connection or dw_url parameter is specified.
    DWSupportConnectionMissingArgument  -- raised if neither
      dwsupport_connection or dwsupport_url parameter is specified

    >>> any_name = 'test_name'
    >>> add_fact( any_name)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.configure.WarehouseConnectionMissingArgument
    """
    # package db locations as keyword argument dicts
    dwsource_args = {'db_url': dw_url, 'connection_func': dw_connection_func}
    dwsupport_args = {'db_url': dwsupport_url
                      ,'connection_func': dwsupport_connection_func}
    # get lists of new items
    items_tuple = _get_fact_items(fact_name, dwsource_args, dwsupport_args)
    # persist the new configuration items
    new_tables, new_variables, new_associations = items_tuple
    try:
        if new_tables:
            dto.table.save(new_tables, **dwsupport_args)
        if new_variables:
            dto.variable.save(new_variables, **dwsupport_args)
        if new_associations:
            dto.association.save(new_associations, **dwsupport_args)
    except ConnectionMissingArgument as e:
        raise DWSupportConnectionMissingArgument(e)

def add_fact_view(fact_name, dw_url=None, dw_connection_func=None
                  ,dwsupport_url=None, dwsupport_connection_func=None):
    """
    Enroll new Fact table (& all neccessary dependant Dimensions/Roles)

    Keyword Parameters:
    fact_name  -- String, representing the name of the fact table which
      is a PostgreSQL view.
    dw_url  --  String, representing a SQLAlchemy connection to the Data
      Warehouse database (Required, if parameter 'dw_connection' is not
      provided)
    connection_func  -- function returning SQLAlchemy connections to the
      database containing Data Warehouse data assets (Optional,
      if provided, will override db_url)
    dwsupport_url  --  String, representing a SQLAlchemy connection to
      the database which contains the DWSupport warehouse model(Required
      , if parameter 'dwsupport_connection' is not provided)
    dwsupport_connection_func  -- function returning SQLAlchemy
      connections to the database containing the DWSupport configuration
      model (Optional, if provided, will override db_url)

    Exceptions:
    WarehouseConnectionMissingArgument  -- raised if neither
      dw_connection or dw_url parameter is specified.
    DWSupportConnectionMissingArgument  -- raised if neither
      dwsupport_connection or dwsupport_url parameter is specified

    >>> any_name = 'test_view_name'
    >>> add_fact( any_name)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.configure.WarehouseConnectionMissingArgument
    """
    # package db locations as keyword argument dicts
    dwsource_args = {'db_url': dw_url, 'connection_func': dw_connection_func}
    dwsupport_args = {'db_url': dwsupport_url
                      ,'connection_func': dwsupport_connection_func}
    # get lists of new items
    items_tuple = _get_fact_view_items(fact_name, dwsource_args, dwsupport_args)
    # persist the new configuration items
    new_tables, new_variables, new_associations = items_tuple
    try:
        if new_tables:
            dto.table.save(new_tables, **dwsupport_args)
        if new_variables:
            dto.variable.save(new_variables, **dwsupport_args)
        if new_associations:
            dto.association.save(new_associations, **dwsupport_args)
    except ConnectionMissingArgument as e:
        raise DWSupportConnectionMissingArgument(e)

def copy_table( source_id, new_project_name, new_table_name
               ,new_custom_id_by_old_ids):
    """
    Add table & related objects to dwsupport,copied from source_id Fact

    Returns 5-tuple, representing new Table DTO and lists of new
      association DTOs, variable DTOs, variable_custom_identifier DTOs
      & query DTOs

    Keyword Parameters:
    source_id  -- Sting, identifying the project Fact table to copy
    new_project_name  -- String, representing project name copy will
      belong to
    new_table_name  -- String, representing name for the new table
    new_custom_id_by_old_ids  -- Dict, representing new custom
      variable IDs, mapped by the existing custom IDs they're replacing

    Exceptions:
    CopyTableUnsupportedTableType  -- unsupported source_id
    CopyTableDuplicateCopyName  -- new_table_name already exists
    CopyTableMissingVariableCustomIdentifiers  -- missing values in
      new_custom_id_by_old_ids
    CopyTableNonuniqueVariableCustomIdentifiers  -- values in
      new_custom_id_by_old_ids are not globally unique
    """
    with warehouse.get_source_model_session() as dwsupport_model:
        # generate DTOs
        new_table, new_associations, new_variables, \
        new_variable_custom_identifiers, new_queries = _copy_fact_table(
             source_id
            ,new_project_name
            ,new_table_name
            ,new_custom_id_by_old_ids
            ,dwsupport_model
        )
        # save DTOs
        get_func = util.get_dwsupport_connection
        dto.table.save([new_table], connection_func=get_func)
        dto.association.save(new_associations, connection_func=get_func)
        dto.variable.save(new_variables, connection_func=get_func)
        dto.variable_custom_identifier.save( new_variable_custom_identifiers
                                            ,connection_func=get_func)
        dto.query.save(new_queries, connection_func=get_func)
        # provide caller with a copy, of the new DTO info
        return new_table, new_associations, new_variables \
            ,new_variable_custom_identifiers, new_queries

def _copy_fact_table( source_id, new_project_name, new_table_name
                     ,new_custom_id_by_old_ids, dwsupport_model):
    """
    Return table & related objects,copied from DWSupport source_id table

    Returns 5-tuple, representing new Table DTO and lists of new
      association DTOs, variable DTOs, variable_custom_identifier DTOs
      & query DTOs

    Keyword Parameters:
    source_id  -- Sting, identifying the project Fact table to copy
    new_project_name  -- String, representing project name copy will
      belong to
    new_table_name  -- String, representing name for the new table
    new_custom_id_by_old_ids  -- Dict, representing new custom
      variable IDs, mapped by the existing custom IDs they're replacing
    dwsupport_model  -- Dict, representing current DWSupport schema

    Exceptions:
    CopyTableUnsupportedTableType  -- unsupported source_id
    CopyTableDuplicateCopyName  -- new_table_name already exists
    CopyTableMissingVariableCustomIdentifiers  -- missing values in
      new_custom_id_by_old_ids
    CopyTableNonuniqueVariableCustomIdentifiers  -- values in
      new_custom_id_by_old_ids are not globally unique

    >>> from pprint import pprint
    >>> # Check generated objects
    >>> source = 'trawl.catch_fact'
    >>> proj = 'trawl' #same project
    >>> table = 'new_catch_fact' #different table name
    >>> custom_ids = {} #none
    >>> model = { 'tables': [ { 'name': 'catch_fact', 'type': 'fact'
    ...                        ,'project': 'trawl'}
    ...                      ,{ 'name': 'depth_dim', 'type': 'dimension'
    ...                        ,'project': 'warehouse'}
    ...                      ,{ 'name': 'operation_fact', 'type': 'fact'
    ...                        ,'project': 'acoustics'}]
    ...          ,'associations': [ { 'table': 'catch_fact'
    ...                              ,'parent': 'depth_dim'}
    ...                            ,{ 'table': 'operation_fact'
    ...                              ,'parent': 'depth_dim'}]
    ...          ,'variables': [ { 'table': 'catch_fact'
    ...                           ,'column': 'retained_kg'}
    ...                         ,{ 'table': 'catch_fact'
    ...                           ,'column': 'retained_ct'}
    ...                         ,{ 'table': 'depth_dim'
    ...                           ,'column': 'meters'}
    ...                         ,{ 'table': 'depth_dim'
    ...                           ,'column': 'fathoms'}
    ...                         ,{ 'table': 'operation_fact'
    ...                           ,'column': 'frequency_mhz'}]
    ...          ,'variable_custom_identifiers': [
    ...               { 'id': 'freq', 'table': 'operation_fact'
    ...                ,'column': 'frequency_mhz'}]
    ...          ,'queries': [
    ...               {'name': 'core',
    ...                'table': 'catch_fact',
    ...                'variables': {'depth_dim': ['meters'],
    ...                              'catch_fact': ['retained_kg']}
    ...               }]
    ... }
    >>> out = _copy_fact_table(source, proj, table, custom_ids, model)
    >>> new_table, new_assocs, new_vars, new_customs, new_queries = out
    >>> pprint(new_table)
    {'name': 'new_catch_fact', 'project': 'trawl', 'type': 'fact'}
    >>> pprint(new_assocs)
    [{'parent': 'depth_dim', 'table': 'new_catch_fact'}]
    >>> pprint(new_vars)
    [{'column': 'retained_kg', 'table': 'new_catch_fact'},
     {'column': 'retained_ct', 'table': 'new_catch_fact'}]
    >>> pprint(new_customs)
    []
    >>> pprint(new_queries)
    [{'name': 'core',
      'table': 'new_catch_fact',
      'variables': {'depth_dim': ['meters'], 'new_catch_fact': ['retained_kg']}}]
    >>> # Check table with a customized field identifier
    >>> source = 'acoustics.operation_fact'
    >>> proj = 'cancelled' #different project
    >>> table = 'bad_operation_fact' # and new, unique table name
    >>> custom_ids = {'freq': 'bad_freq', 'extra_mapping': 'ignored'}
    >>> out = _copy_fact_table(source, proj, table, custom_ids, model)
    >>> new_table, new_assocs, new_vars, new_customs, new_queries = out
    >>> pprint(new_table)
    {'name': 'bad_operation_fact', 'project': 'cancelled', 'type': 'fact'}
    >>> pprint(new_assocs)
    [{'parent': 'depth_dim', 'table': 'bad_operation_fact'}]
    >>> pprint(new_vars)
    [{'column': 'frequency_mhz', 'table': 'bad_operation_fact'}]
    >>> pprint(new_customs)
    [{'column': 'frequency_mhz', 'id': 'bad_freq', 'table': 'bad_operation_fact'}]
    >>> pprint(new_queries)
    []
    >>> # Check ambiguous table name
    >>> table = 'operation_fact' #same name as 'acoustics' project table
    >>> _copy_fact_table(source, proj, table, custom_ids, model)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.configure.CopyTableDuplicateCopyName: operation_fact
    """
    source_project, source_table = source_id.split('.')
    # create Table DTO
    source_table_generator = (t for t in dwsupport_model['tables']
                              if t['name'] == source_table
                              and t['project'] == source_project)
    all_table_names_generator = (t['name'] for t in dwsupport_model['tables'])
    new_table = dict(next(source_table_generator)) #construct a new dict
    new_table['name'] = new_table_name
    new_table['project'] = new_project_name
    if new_table['type'] != 'fact':
        raise CopyTableUnsupportedTableType(new_table['type'])
    if new_table_name in all_table_names_generator:
        raise CopyTableDuplicateCopyName(new_table_name)
    # create Variable DTOs
    def _set_table(dto_with_table):
        dto_with_table['table'] = new_table_name
        return dto_with_table
    new_variables = [_set_table(v) for v
                     in dwsupport_model['variables']
                     if v['table'] == source_table]
    # create Variable Custom Identifier DTOs
    new_variable_custom_identifiers = [
        custom for custom
        in dwsupport_model['variable_custom_identifiers']
        if custom['table'] == source_table]
    # (error if a custom identifier not in input parameters)
    existing_ids = {c['id'] for c in new_variable_custom_identifiers}
    unmapped_existing_ids = existing_ids.difference(
        set(new_custom_id_by_old_ids.keys())
    )
    if unmapped_existing_ids != set():
        needs_values = json.dumps(
            {key: "PROVIDE_NEW_UNIQUE_VALUE" #example, to prompt the user
             for key in unmapped_existing_ids}
        )
        raise CopyTableMissingVariableCustomIdentifiers(needs_values)
    # (error if any proposed IDs are not unique)
    nonunique_ids = set()
    input_repeats_ids = set()
    for new_id, count_in_input in Counter(new_custom_id_by_old_ids.values()).items():
        if new_id in existing_ids:
            nonunique_ids.add(new_id)
        if count_in_input > 1:
            input_repeats_ids.add(new_id)
    all_duplicates = nonunique_ids.union(input_repeats_ids)
    if all_duplicates != set():
        raise CopyTableNonuniqueVariableCustomIdentifiers(all_duplicates)
    for custom in new_variable_custom_identifiers:
        key = custom['id']#existing custom variable identifier
        new_id = new_custom_id_by_old_ids[key]
        custom['id'] = new_id
        custom['table'] = new_table_name
    # create Association DTOs
    new_associations = [_set_table(a) for a
                        in dwsupport_model['associations']
                        if a['table'] == source_table]
    # create Query DTOs
    new_queries = [_set_table(q) for q
                        in dwsupport_model['queries']
                        if q['table'] == source_table]
    for new_query in new_queries:
        # update the variable table names too (if any)
        for table_name, column_list in new_query['variables'].items():
            if table_name == source_table:
                # transfer columns to new table name
                new_query['variables'][new_table_name] = column_list
                # delete query's list of columns from original table
                del(new_query['variables'][source_table])
    return new_table, new_associations, new_variables, \
        new_variable_custom_identifiers, new_queries

def _get_fact_items(fact_name, dwsource_args, dwsupport_args):
    """
    returns new tables, associations & variables lists to configure fact

    Keyword Parameters:
    fact_name  -- String, representing the name of the fact table to add
    dwsource_args  -- Dict, representing DWSupport connection parameters
      referencing Data Warehouse database location.
    dwsupport_args  -- Dict, representing DWSupport connection parameters
      indicating location of warehouse model

    Exceptions:
    WarehouseConnectionMissingArgument  -- raised if dwsource_args is
      incomplete
    DWSupportConnectionMissingArgument  -- raised if dwsupport_args is
      incomplete

    >>> any_name = 'test_name'
    >>> empty_config = {}
    >>> _get_fact_items( any_name, empty_config, empty_config)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.configure.WarehouseConnectionMissingArgument
    """
    # 1) add tables
    # create Table obj for fact
    fact_table = {'name': fact_name, 'type': 'fact', 'project':None
                  ,'updated': None, 'rows': None, 'contact': None
                  ,'years': None}
    # discover any potential new tables this fact depends on
    try:
        discovered_tables = discover.lookup_tables( [fact_name], **dwsource_args)
    except ConnectionMissingArgument as e:
        raise WarehouseConnectionMissingArgument(e)
    # check which potentials, are actually new
    try:
        configured_tables = dto.table.get(**dwsupport_args)
    except ConnectionMissingArgument as e:
        raise DWSupportConnectionMissingArgument(e)
    dwsupport_name_type_tuples = [(t['name'], t['type'])
                                  for t in configured_tables]
    potential_new_tables = [fact_table]+discovered_tables
    new_tables = [t for t in potential_new_tables
                  if (t['name'],t['type']) not in dwsupport_name_type_tuples]

    # 2) add variables
    new_table_names = [t['name'] for t in new_tables]
    try:
        discovered_variables = dto.variable.get_by_lookup(new_table_names
                                                          ,**dwsource_args)
    except ConnectionMissingArgument as e:
        raise WarehouseConnectionMissingArgument(e)
    # ignore any fact fields, which seem like OLAP dimensional lookups
    new_variables = [v for v in discovered_variables
                     if not v['column'].endswith(dimension_lookup_suffix)]

    # 3) add OLAP dimensional associations
    try:
        discovered_associations =discover.lookup_associations([fact_name]
                                                              ,**dwsource_args)
    except ConnectionMissingArgument as e:
        raise WarehouseConnectionMissingArgument(e)
    # determine which discovered assocations are new
    discovered_non_rolebases = [a for a in discovered_associations
                                if not a['type']=='dimension role base']
    discovered_rolebases = [a for a in discovered_associations
                            if a['type']=='dimension role base']
    # some Dimension Role Bases may already be configured
    try:
        configured_associations = dto.association.get_all(**dwsupport_args)
    except ConnectionMissingArgument as e:
        raise DWSupportConnectionMissingArgument(e)
    new_rolebases = [a for a in discovered_rolebases
                     if a not in configured_associations]
    all_new_associations = discovered_non_rolebases+new_rolebases
    return new_tables, new_variables, all_new_associations

def _get_fact_view_items(fact_name, dwsource_args, dwsupport_args):
    """
    returns new tables, associations & variables lists to configure fact

    Keyword Parameters:
    fact_name  -- String, representing the name of the fact table which
      is a PostgreSQL view.
    dwsource_args  -- Dict, representing DWSupport connection parameters
      referencing Data Warehouse database location.
    dwsupport_args  -- Dict, representing DWSupport connection parameters
      indicating location of warehouse model

    Exceptions:
    WarehouseConnectionMissingArgument  -- raised if dwsource_args is
      incomplete
    DWSupportConnectionMissingArgument  -- raised if dwsupport_args is
      incomplete

    >>> any_name = 'test_view_name'
    >>> empty_config = {}
    >>> _get_fact_items( any_name, empty_config, empty_config)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.configure.WarehouseConnectionMissingArgument
    """
    # 1) add tables
    # create Table obj for fact
    fact_table = {'name': fact_name, 'type': 'fact', 'project':None
                  ,'updated': None, 'rows': None, 'contact': None
                  ,'years': None}
    # retrieve the list of view fields.
    try:
        discovered_variables = dto.variable.get_by_lookup([fact_name]
                                                          ,**dwsource_args)
    except ConnectionMissingArgument as e:
        raise WarehouseConnectionMissingArgument(e)
    # identify which fields are variables & which may be Dimensional lookups
    new_variables, potential_lookups = [], []
    for var in discovered_variables:
        if var['column'].endswith(dimension_lookup_suffix):
            potential_lookups.append(var)
            continue #skip, to the next variable
        new_variables.append(var) #otherwise, seems like a measured value!
    assert len(new_variables)+len(potential_lookups)==len(discovered_variables)

    # identify known Dimensional or Roles that match a potential lookup field
    try:
        current_tables = dto.table.get(**dwsupport_args)
        current_associations = dto.association.get_all(**dwsupport_args)
    except ConnectionMissingArgument as e:
        raise DWSupportConnectionMissingArgument(e)
    current_tables_by_name = {} #build a map of all Dimensions/Roles
    for known_table in current_tables:
        table_type, name = known_table['type'], known_table['name']
        if table_type in ('dimension', 'dimension role'):
            current_tables_by_name[name] = known_table
    dim_pk_fields_by_role_name = {} #build a map of Dimension pk field names
    role_base_relations = [r for r in current_associations
                           if r['type']=='dimension role base']
    for role_base_relation in role_base_relations:
        role_name = role_base_relation['table']
        dim_pk_field = role_base_relation['parent_column']
        dim_pk_fields_by_role_name[role_name] = dim_pk_field

    new_associations, unrecognized_lookups = [], []
    for discovered_variable in potential_lookups:
        field = discovered_variable['column']
        possible_table_name = field.replace(dimension_lookup_suffix,'_dim')
        try:
            matching_table = current_tables_by_name[possible_table_name]
        except KeyError: #table not recognized
            unrecognized_lookups.append(discovered_variable)
            continue
        matching_lookup_name = matching_table['name']
        try: #if matching table is a Role, use the pk field of underlying dim
            lookup_column = dim_pk_fields_by_role_name[matching_lookup_name]
        except KeyError: #lookup not recognized as a configured Role
            lookup_column = matching_lookup_name.replace('_dim'
                                                        ,dimension_lookup_suffix)
        view_association = {'parent': matching_lookup_name
                            ,'parent_column': lookup_column
                            ,'table': fact_name, 'column': field
                            ,'type':'fact {}'.format(matching_table['type'])}
        new_associations.append( view_association)
    assert len(new_associations)+len(unrecognized_lookups)==len(potential_lookups)
    
    # for now, just indicate that a new table for the View is needed
    new_tables = [fact_table] #TODO: process unrecognized_lookups,for additional tables+associations
    msg = ('TODO: Configuring entirely new roles/dimensions is not yet'
           ' implemented!')
    assert len(unrecognized_lookups) == 0, msg
    return new_tables, new_variables, new_associations
