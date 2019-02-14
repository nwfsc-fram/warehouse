"""
Module defining helper functions for "defaults=" selection parameter

Copyright (C) 2016-2017 ERT Inc.
"""
from pprint import pformat

from ..warehouse import util, warehouse
from . import parameters

PARAMETER_NAME = parameters.ReservedParameterNames.defaults
#String,representing the URL query param for specifying default query

DEFAULT_QUERY_HIERARCHY = [
     'core'
    ,'expanded'
]
#List, representing which Query to use in descending order if no default/variables specified

class UndefinedDefaultQuery(KeyError):
    """
    Defaults= selection value is unrecognized for this source
    """
    pass

class AmbiguousDefaultQuery(ValueError):
    """
    Two or more values are specified for Defaults= selection
    """
    pass

class NoQueriesDefined(KeyError):
    """
    No queries are defined for this source
    """
    pass

class AmbiguousQueryHierarchy(ValueError):
    """
    Source has two or more queries but none are assigned priority
    """
    pass

def get_query_name_from_hierarchy(queries_for_this_source):
    """
    Return the preferred query, when no defaults parameter is specified

    DEFAULT_QUERY_HIERARCHY in this module defines the order in which
    queries should be used, as default variables for selection. If only
    one query is defined, that is the one that will be returned.

    Exceptions:
    NoQueriesDefined  -- No queries are defined for this source
    AmbiguousQueryHierarchy  -- Hierarchy does not indicate which query
      to use as default (and more than 1x query is defined)

    >>> core_queries = [{'name': 'something'}, {'name': 'core'}]
    >>> get_query_name_from_hierarchy(core_queries)
    'core'
    >>> expanded_queries = [ {'name': 'expanded'}
    ...                     ,{'name': 'something2'}]
    >>> get_query_name_from_hierarchy(expanded_queries)
    'expanded'
    >>> both_queries = [ {'name': 'expanded'}, {'name': 'something2'}
    ...                 ,{'name': 'core'}]
    >>> get_query_name_from_hierarchy(both_queries)
    'core'
    >>> one_query = [{'name': 'something3'}]
    >>> get_query_name_from_hierarchy(one_query)
    'something3'
    >>> #Check when queries have unclear priority, or are undefined
    >>> unclear_queries = [ {'name': 'NotClearlyBetter'}
    ...                    ,{'name': 'ThanTheOther'}]
    >>> get_query_name_from_hierarchy(unclear_queries)
    Traceback (most recent call last):
       ...
    api.resources.source.selection.defaults.AmbiguousQueryHierarchy: ['NotClearlyBetter', 'ThanTheOther']
    >>> no_queries = []
    >>> get_query_name_from_hierarchy(no_queries)
    Traceback (most recent call last):
       ...
    api.resources.source.selection.defaults.NoQueriesDefined
    """
    #identify queries for this Source
    defined_query_names = [q['name'] for q in queries_for_this_source]

    #return the query that is preferred
    for name in DEFAULT_QUERY_HIERARCHY:
        if name in defined_query_names:
            return name

    #otherwise
    if len(defined_query_names) == 1:
        return defined_query_names.pop() #return the only defined query
    if len(defined_query_names) > 1:
        raise AmbiguousQueryHierarchy(defined_query_names) #TODO: add functional tests
    #else
    raise NoQueriesDefined()

def get_default_query_ids(source_id, model):
    """
    Returns set of Strings, representing source_id's default queries

    Keyword Parameters:
    source_id  -- String, representing API ID of the selection source
    model  -- Dict, representing current DWSupport configuration

    >>> from copy import deepcopy
    >>> no_query_model = { 'queries': []
    ...                   ,'associations': []
    ...                   ,'tables': [{'name': 'foo_fact', 'type': 'fact'}]
    ...                   ,'variables': [ { 'table': 'foo_fact'
    ...                                    ,'column': 'foo_ml'}]
    ...                   ,'variable_custom_identifiers': []}
    >>> source = 'my_example.foo_fact'
    >>> # Check unspecified 'defaults' on a source without 'queries'
    >>> empty_defaults = []
    >>> get_default_query_ids(source, no_query_model)
    set()
    >>> # Check a source with a 'query'
    >>> test_model = { 'queries': [{ 'table': 'foo_fact', 'name': 'core'
    ...                             ,'variables': {'foo_fact': ['foo_ml']}
    ...                            }]
    ...               ,'associations': []
    ...               ,'tables': [{'name': 'foo_fact', 'type': 'fact'}]
    ...               ,'variables': [ { 'table': 'foo_fact'
    ...                                ,'column': 'foo_ml'}
    ...                              ,{ 'table': 'foo_fact'
    ...                                ,'column': 'foo_operation_code'}]
    ...               ,'variable_custom_identifiers': []}
    >>> get_default_query_ids(source, test_model)
    {'core'}
    >>> # Check a source with multiple 'queries'
    >>> multiple_query_model = deepcopy(test_model)
    >>> multiple_query_model['queries'].append({
    ...     'table': 'foo_fact'
    ...     ,'name': 'everything'
    ...     ,'variables': {
    ...          'foo_fact': [
    ...              'foo_ml'
    ...             ,'foo_operation_code']}
    ... })
    >>> defaults_output = get_default_query_ids(source, multiple_query_model)
    >>> defaults_output == {'core', 'everything'}
    True
    """
    defaults = set()
    source_project, source_table_name = source_id.split('.')

    for query in model['queries']:
        if query['table'] == source_table_name: #add it
            set_of_one_identifier_name_to_add = {query['name']}
            defaults.update(set_of_one_identifier_name_to_add)
    return defaults

def get_default_variables(defaults, source_id, model):
    """
    Returns list of strings, representing selection default variable IDs
    
    Keyword Parameters:
    defaults  -- List of strings, representing requested default query
      names
    source_id  -- String, representing API ID of the selection source
    model  -- Dict, representing current DWSupport configuration

    >>> from copy import deepcopy
    >>> no_query_model = { 'queries': []
    ...                   ,'associations': []
    ...                   ,'tables': [{'name': 'foo_fact', 'type': 'fact'}]
    ...                   ,'variables': [{ 'table': 'foo_fact'
    ...                                   ,'column': 'foo_ml'}]
    ...                   ,'variable_custom_identifiers': []}
    >>> source = 'my_example.foo_fact'
    >>> # Check unspecified 'defaults' on a source without 'queries'
    >>> empty_defaults = []
    >>> get_default_variables(empty_defaults, source, no_query_model)
    []
    >>> # Check unspecified 'defaults' on a source with a 'query'
    >>> test_model = { 'queries': [{ 'table': 'foo_fact', 'name': 'core'
    ...                             ,'variables': {'foo_fact': ['foo_ml']}
    ...                            }]
    ...               ,'associations': []
    ...               ,'tables': [{'name': 'foo_fact', 'type': 'fact'}]
    ...               ,'variables': [ { 'table': 'foo_fact'
    ...                                ,'column': 'foo_ml'}
    ...                              ,{ 'table': 'foo_fact'
    ...                                ,'column': 'foo_operation_code'}]
    ...               ,'variable_custom_identifiers': []}
    >>> get_default_variables(empty_defaults, source, test_model)
    ['foo_ml']
    >>> # Check a specified 'defaults',
    >>> defaults = ['core'] #expect the same result
    >>> get_default_variables(defaults, source, test_model)
    ['foo_ml']
    >>> # Check 'defaults' with a dimensional field
    >>> fact_dim_model = deepcopy(test_model)
    >>> fact_dim_model['variables'].append(
    ...     {'table': 'bar_dim', 'column': 'bar_date'})
    >>> fact_dim_model['tables'].append(
    ...     {'name': 'bar_dim', 'type': 'dimension'})
    >>> fact_dim_model['associations'].append(
    ...     {'table': 'foo_fact', 'parent': 'bar_dim', 'type': 'fact dimension'})
    >>> fact_dim_model['queries'][0]['variables']['bar_dim'] = ['bar_date']
    >>> list_variables = get_default_variables(defaults, source, fact_dim_model)
    >>> list_variables.sort() #stabilize ordering, for test
    >>> list_variables
    ['bar_dim$bar_date', 'foo_ml']
    >>> # Check 'defaults' with a custom Variable ID
    >>> custom_model = deepcopy(test_model)
    >>> custom_model['variable_custom_identifiers'] = [
    ...     {'table': 'foo_fact', 'column': 'foo_ml', 'id': 'foo'}]
    >>> get_default_variables(defaults, source, custom_model)
    ['foo']
    >>> # Check a 'defaults' query that is not defined in the model
    >>> undefined_defaults = ['other'] #expect an exception
    >>> get_default_variables(undefined_defaults, source, test_model)
    Traceback (most recent call last):
       ...
    api.resources.source.selection.defaults.UndefinedDefaultQuery: 'other'
    >>> # Check a 'defaults' where more than one query is specified
    >>> bad_defaults = ['core', 'other'] #expect an exception
    >>> get_default_variables(bad_defaults, source, test_model)
    Traceback (most recent call last):
       ...
    api.resources.source.selection.defaults.AmbiguousDefaultQuery: ['core', 'other']
    """
    default_variables = []
    source_project, source_table_name = source_id.split('.')

    #0) identify requested Query name
    deduplicated_defaults = set(defaults)
    if len(deduplicated_defaults) > 1:
        # Riase an error, if defaults parameter has more than 1x unique Query
        unique_query_names = list(deduplicated_defaults)
        unique_query_names.sort()#stabilze ordering
        raise AmbiguousDefaultQuery(unique_query_names)

    queries_for_this_source = [q for q in model['queries'] if q['table'] == source_table_name]
    try:
        default_query_name = deduplicated_defaults.pop()
        explicit_defaults_requested = True
    except KeyError as empty_deduplicated_list_exception:
        explicit_defaults_requested = False #no specific default was listed
        #when default query is unspecified, select one from hierarchy
        try:
            default_query_name = get_query_name_from_hierarchy(queries_for_this_source)
        except NoQueriesDefined as source_has_no_queries_exception:
            #No queries have been defined, so specify no fields
            return []

    #1) retrieve default query
    physical_columns_by_table_name = {}
    for query in queries_for_this_source:
        if query['name'] == default_query_name:
            physical_columns_by_table_name = query['variables']
            break
    else:
        if explicit_defaults_requested:
            raise UndefinedDefaultQuery(default_query_name)

    #2) Translate the tables+physical column names into Source field IDs
    variables_by_column = {v['column']:v for v in model['variables']}
    table_types_by_name = {t['name']:t['type'] for t in model['tables']}#TODO:is this needed?
    fact_web_ids_by_table_and_column_tuples = None
    if table_types_by_name[source_table_name] == 'fact':
        for table_dto in model['tables']:
            if table_dto['name'] == source_table_name:
                source_table = table_dto
                break
        mapping = _map_table_column_tuples_to_web_ids(source_table, model)
        fact_web_ids_by_table_and_column_tuples = mapping
    if any(physical_columns_by_table_name):
        for table_name, physical_column_names in physical_columns_by_table_name.items():
            for column_name in physical_column_names:
                web_id = column_name
                #2a) prefix variable names, if source is a Fact cube
                if fact_web_ids_by_table_and_column_tuples is not None:
                    lookup_key = (table_name, column_name)
                    web_id = fact_web_ids_by_table_and_column_tuples[lookup_key]
                #2b) apply custom identifiers
                # override the variable 'table',since query may refer to Role
                munged_variable = dict(variables_by_column[column_name])#copy
                munged_variable['table'] = table_name
                custom_id = util.get_custom_variable_name(munged_variable, model)
                if custom_id is not None:
                    web_id = custom_id
                #2c) limit maximum length of name
                max_pgsql_field_name_length = 63 #TODO: this should be integrated into 'variables' output as well
                default_variables.append(web_id[:max_pgsql_field_name_length])
    return default_variables

def _map_table_column_tuples_to_web_ids(fact_selection_table, model):
    """
    utility, returns Dict mapping table+physcial_column tuples to web_id

    Keyword Parameters:
    fact_selection_table  -- Dict, representing a DWSupport table Fact
      that default variables are being looked up for
    model  -- Dict, representing the full DWSupport configuration

    >>> from pprint import pprint
    >>> test_fact = {'name': 'foo_fact', 'type': 'fact'}
    >>> test_model = { 'associations': [{ 'table': 'foo_fact'
    ...                                  ,'parent': 'sample_dim'
    ...                                  ,'type': 'fact dimension'}]
    ...               ,'tables': [ test_fact
    ...                           ,{ 'name': 'sample_dim'
    ...                             ,'type': 'dimension'}]
    ...               ,'variable_custom_identifiers': [
    ...                     { 'table': 'foo_fact'
    ...                      ,'column': 'measure_two'
    ...                      ,'id': 'customized_measure_id'}]
    ...               ,'variables': [ { 'table': 'foo_fact'
    ...                                ,'column': 'measure_one'}
    ...                              ,{ 'table': 'foo_fact'
    ...                                ,'column': 'measure_two'}
    ...                              ,{ 'table': 'sample_dim'
    ...                                ,'column': 'field_one'}]}
    >>> out = _map_table_column_tuples_to_web_ids(test_fact, test_model)
    >>> pprint(out)
    {('foo_fact', 'measure_one'): 'measure_one',
     ('foo_fact', 'measure_two'): 'customized_measure_id',
     ('sample_dim', 'field_one'): 'sample_dim$field_one'}
    """
    #get Fact info
    fact_variables, fact_physical_columns = warehouse.get_fact_variables(fact_selection_table, model)

    # summarize which table+column pair the web_ids correspond with
    web_ids_by_table_and_column_tuples = {}
    for web_id in fact_variables:
        fact_variable = fact_variables[web_id]
        table_name = fact_variable['table']

        physical_column_name = fact_physical_columns[web_id]

        key = (table_name, physical_column_name)
        web_ids_by_table_and_column_tuples[key] = web_id
    # return mapping
    return web_ids_by_table_and_column_tuples
