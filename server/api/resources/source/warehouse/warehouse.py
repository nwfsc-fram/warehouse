"""
Module, emulating a fused Warehouse dataset containing data from all sources.

Warehouse dataset is emulated here in Python, since PostgreSQL warehouse schema
is not yet available/completed.

Copyright (C) 2015-2016, 2018 ERT Inc.
"""
import contextlib

import numpy
import sqlalchemy as sql
import sqlalchemy.dialects.postgresql as postgresql

from api.resources import source
from api.resources.source.selection import parameters, auth
from api.resources.source.warehouse import util, sqlgenerator
from api.resources.source.warehouse.support.dto import (
                                                          variable
                                                        , table
                                                        , table_type
                                                        , association
                                                       )
from api.resources.source.warehouse.support.model import prefetch_cache
import api.json as json
import api.config_loader

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

str_warehouse_id = 'warehouse'
#String identifier reserved for the combined Data Warehouse source

str_warehouse_name = 'Data Warehouse'
#String providing a human-readable name for the Data Warehouse

str_warehouse_description = 'Integrated representation of all other data sets'
#String providing a human-readable description of the Data Warehouse contents

str_warehouse_project = 'warehouse'
#String providing a human-readable description of the Data Warehouse owner

str_warehouse_contact = 'Name: FRAM Data Team <nmfs.nwfsc.fram.data.team@noaa.gov>'
#String providing a human-readable contact info for the Data Warehouse owner

str_no_data_placeholder = 'NaN'
#String value, to represent when No Data was available for a particular field

dict_source = {'id':'Fake .ini source','db_file':'db_config.ini'}
#Dict, conformed to server/etl_config.ini format &specifying db config location

def is_warehouse( str_id):
    """
    Utility function to check if the referenced data source ID is a warehouse

    Return Boolean -- ID status

    >>> is_warehouse( 'warehouse')
    True
    >>> is_warehouse( 'warehouse1') #"warehouse" is only reserved/valid name
    False
    >>> is_warehouse( 'WarEhousE') #sources require exact case
    False
    """
    return str_id == str_warehouse_id

def get_result(api_session_user, variables=[], filters=[]):
    """
    returns list of db result rows, w/ 1x 'header' row prepended

    Keyword Parameters:
    api_session_user  -- String, representing unique ID for current API
     session user
    variables  -- list of requested variables
    filters  -- list of requested filters

    Exceptions:
    FilterVariableError -- filters variable not found in header

    """
    # retrieve intermediate resultsets from each source
    with get_source_model_session() as current_model:
        results_by_id = {}
        for dict_source in source.source.SourceUtil.get_list_of_data_sources(
                request.url
                ,api_session_user
                ,current_model
                ,include_dims=False):
            str_source_id = dict_source['id']
            if not is_warehouse( str_source_id):
                result = get_result_for_one_source( str_source_id, variables, filters)
                results_by_id[str_source_id] = result
        # combine intermediate resultsets
        list_result = get_source_results_combined( results_by_id)
        # subset returned fields to only the requested ones
        return parameters.get_result_subset(list_result, variables)

def get_result_for_one_source( str_source_id, variables_all=[], filters_all=[]):
    """
    returns list of db result rows, w/ 1x 'header' row prepended

    Keyword Parameters:
    str_source_id -- String, representing the API id ({project_id}.{fact_name})
        of the fact "cube" variables will be returned for.
    variables_all  -- list of names, for every Warehouse variable requested
        by the User.
    filters_all  --  list of strings, representing every URL query filter
        specified by the User.

    Exceptions:
    ValueError -- No datasource found for str_source_id

    """
    #1) separate filters and variables, by data source
    try:
        # check if source is a non-static 'fact' datasource.
        dict_source = source.data._get_dict_source( str_source_id)
        variables = get_variables_by_source_id( str_source_id, variables_all)
        filters = get_filters_by_source_id( str_source_id, filters_all)
    except source.data.NoStaticSource:
        # locate non-static
        for t in get_source_tables():
            t_id = '{project}.{name}'.format( **t )
            if t['type'] == 'fact' and t_id == str_source_id:
                #separate filters/variables for dynamic source(joined fact+dims)
                import api.resources.source.variables as variables #FIXME: refactor circular dependency between variables & warehouse
                fact_variables = variables.get_list_of_variables(str_source_id)
                variables = _get_variables_by_fact_id( str_source_id
                                                      ,fact_variables
                                                      ,variables_all)
                filters = _get_filters_by_fact_id( str_source_id
                                                  ,fact_variables
                                                  ,filters_all)
                break
        else:
            raise ValueError("No datasource found by that name") #TODO: make this a local class
    #2) retrieve intermediate resultsets from each source
    return source.data.get_data( str_source_id, variables, filters)

def get_variables_by_source_id( str_source_id, variables_all=[]):
    """
    Utility function, returns variables relevant to one underlying datasource

    Exceptions:
    api.resources.source.selection.parameters.FilterParseError -- unrecognized filter
        expression.

    >>> list_warehouse_vars =['proj1.set1$time','proj2.set1$hot']
    >>> get_variables_by_source_id('proj1.set1', list_warehouse_vars)
    ['time']
    >>> get_variables_by_source_id('proj2.set1', list_warehouse_vars)
    ['hot']
    >>> get_variables_by_source_id('proj2.set9', list_warehouse_vars)
    []
    """
    list_variables_for_source = []
    for str_warehouse_variable in variables_all:
        tuple_name = get_warehouse_field_name_partitioned( str_warehouse_variable)
        str_filter_source, str_separator, str_field_name = tuple_name
        if str_source_id == str_filter_source:
            list_variables_for_source.append( str_field_name)
    return list_variables_for_source

def _get_variables_by_fact_id( source_id, source_variables, all_api_variables=[]):
    """
    Utility function, returns variables relevant to one Warehouse fact cube

    Keyword Parameters:
    source_id  --  String, representing the API id ({project_id}.{fact_name})
        of the fact "cube" variables will be returned for.
    source_variables  -- list of dwsupport 'variable' Data Transfer Objects
        representing all the available 'source_id' fields.
    all_api_variables  -- list of names, for every Warehouse variable requested
        by the User.

    >>> proj1_vars = ["airspeed_kph","time_dim$time"]
    >>> proj2_vars = ["hot"]
    >>> list_warehouse_vars =['time_dim$time','proj1.set1$airspeed_kph'\
            ,'proj2.set1$hot']
    >>> _get_variables_by_fact_id('proj1.set1', proj1_vars, list_warehouse_vars)
    ['time_dim$time', 'airspeed_kph']
    >>> _get_variables_by_fact_id('proj2.set1', proj2_vars, list_warehouse_vars)
    ['hot']
    >>> _get_variables_by_fact_id('proj2.set9', proj2_vars, list_warehouse_vars)
    []
    """
    relevant_variables = []
    # identify relevant variables
    measures_by_prefixed_name = _get_measures_by_prefixed_name( source_id
                                                             ,source_variables)
    for api_variable in all_api_variables:
        # see if variable matches Dimension from our"cube"(i.e.:fact+dim joins)
        if api_variable in source_variables:
            relevant_variables.append( api_variable)
            continue
        # see if variable matches a measure from our"cube"(i.e.:fact+dim joins)
        if api_variable in measures_by_prefixed_name.keys():
            relevant_variables.append( measures_by_prefixed_name[api_variable])
            continue
    return relevant_variables

def _get_measures_by_prefixed_name(source_id, source_variable_names):
    """
    Utility function,returns a Dict of measure names for source,indexed by {source_id}${measure_name}

    Keyword Parameters:
    source_id  --  String, representing API id for the data source
    source_variable_names  -- list of strings, representing API id's for all
        fields available in the referenced data source.

    >>> from pprint import pprint
    >>> vars1 = ["airspeed_kph","time_dim$time"]
    >>> dict1 = _get_measures_by_prefixed_name( 'proj1.set1', vars1)
    >>> pprint( dict1)
    {'proj1.set1$airspeed_kph': 'airspeed_kph'}
    """
    separator = util.str_source_variable_separator
    measures = [var for var in source_variable_names if (separator not in var) ]
    measures_by_prefixed_name = { util.prefix_field_name(name, source_id): name
                                  for name in measures} # build dict
    return measures_by_prefixed_name

def get_filters_by_source_id( str_source_id, filters_all=[]):
    """
    Utility function, returns filters relevant to one underlying datasource

    Exceptions:
    api.resources.source.selection.parameters.FilterParseError -- unrecognized filter
        expression.

    >>> list_warehouse_filt =['proj1.set1$time>=01/15/1999','proj2.set1$hot=N']
    >>> get_filters_by_source_id('proj1.set1', list_warehouse_filt)
    ['time>=01/15/1999']
    >>> get_filters_by_source_id('proj2.set1', list_warehouse_filt)
    ['hot=N']
    >>> get_filters_by_source_id('proj2.set9', list_warehouse_filt)
    []
    """
    list_filters_for_source = []
    for str_filter in filters_all:
        list_filter_elements = parameters.get_list_filter_partitioned(str_filter)
        #FIXME: validate 'list_filter_elements' assumptions below
        #Assume left-hand side of the filter expression was the variable name
        str_wh_variable,str_operator,str_value = list_filter_elements
        tuple_name = get_warehouse_field_name_partitioned( str_wh_variable)
        str_filter_source, str_separator, str_field_name = tuple_name
        if str_source_id == str_filter_source:
            str_filter_new = '{}{}{}'.format(str_field_name,str_operator,str_value)
            list_filters_for_source.append( str_filter_new)
    return list_filters_for_source

def _get_filters_by_fact_id( source_id, source_variables, all_api_filters=[]):
    """
    Utility function, returns variables relevant to one Warehouse fact cube

    Keyword Parameters:
    source_id  --  String, representing the API id ({project_id}.{fact_name})
        of the fact "cube" variables will be returned for.
    source_variables  -- list of dwsupport 'variable' Data Transfer Objects
        representing all the available 'source_id' fields.
    all_api_filters  --  list of strings, representing every URL query filter
        specified by the User.

    Exceptions:
    api.resources.source.selection.parameters.FilterParseError -- unrecognized filter
        expression.

    >>> proj1_vars = ["airspeed_kph","time_dim$time"] #all columns of p1 set 1
    >>> proj2_vars = ["hot"] #all columns of p2 dataset 1
    >>> list_warehouse_filt =[ 'time_dim$time>=01/15/1999','proj2.set1$hot=N' \
                              ,'proj1.set1$airspeed_kph<100']
    >>> _get_filters_by_fact_id('proj1.set1', proj1_vars, list_warehouse_filt)
    ['time_dim$time>=01/15/1999', 'airspeed_kph<100']
    >>> _get_filters_by_fact_id('proj2.set1', proj2_vars, list_warehouse_filt)
    ['hot=N']
    >>> _get_filters_by_fact_id('proj2.set9', proj2_vars, list_warehouse_filt)
    []
    """
    filters_for_source = []
    # identify relevant filters
    measures_by_prefixed_name = _get_measures_by_prefixed_name( source_id
                                                             ,source_variables)
    for api_filter in all_api_filters:
        filter_elements = parameters.get_list_filter_partitioned(api_filter)
        #FIXME: validate 'list_filter_elements' assumptions below
        #Assume left-hand side of the filter expression was the variable name
        api_variable,operator,value = filter_elements
        # see if variable matches Dimension from our"cube"(i.e.:fact+dim joins)
        if api_variable in source_variables:
            # great! simply use the API filter,unmodified.(cube will recognize)
            filters_for_source.append( api_filter)
            continue
        # see if variable matches a measure from our"cube"(i.e.:fact+dim joins)
        if api_variable in measures_by_prefixed_name.keys():
            filter_field_name = measures_by_prefixed_name[api_variable]
            fact_filter = '{}{}{}'.format(filter_field_name,operator,value)
            filters_for_source.append( fact_filter)
            continue
    return filters_for_source

def get_warehouse_field_name_partitioned( str_warehouse_field_name):
    """
    Utility function to split Warehouse fields into component parts

    Exceptions:
    api.resources.source.selection.parameters.FilterParseError -- too many separators
        present in field name, or underlying dataset field name is too short.

    >>> str_field1 = "proj1.dataset1"+util.str_source_variable_separator+"air_speed"
    >>> get_warehouse_field_name_partitioned( str_field1)
    ('proj1.dataset1', '$', 'air_speed')
    >>> str_field2 = util.str_source_variable_separator.join(['get','quick.plan1','vault_type'])
    >>> get_warehouse_field_name_partitioned( str_field2)
    Traceback (most recent call last):
    ...
    api.resources.source.selection.parameters.FilterParseError: Cannot parse: get$quick.plan1$vault_type
    >>> str_field3 = util.str_source_variable_separator.join(['getCashQuick.plan1','vault_type'])
    >>> get_warehouse_field_name_partitioned( str_field3)
    ('getCashQuick.plan1', '$', 'vault_type')
    >>> str_field4 = util.str_source_variable_separator.join(['getCashQuick.plan1',''])
    >>> get_warehouse_field_name_partitioned( str_field4)
    Traceback (most recent call last):
    ...
    api.resources.source.selection.parameters.FilterParseError: Cannot parse: getCashQuick.plan1$
    """
    str_separator = util.str_source_variable_separator
    # check if warehouse field name has only 1 and only 1 separator
    if not str_warehouse_field_name.count(str_separator) == 1:
        raise parameters.FilterParseError('Cannot parse: '+str_warehouse_field_name)
    # else, parse field
    tuple_field_substrings = str_warehouse_field_name.partition( str_separator)
    if len(tuple_field_substrings[2]) < 1:
        raise parameters.FilterParseError('Cannot parse: '+str_warehouse_field_name)
    #Else, field name successfully separated from source id!
    return tuple_field_substrings

def get_source_results_combined( dict_results_by_id):
    """
    Utility function,to combine a collection of DBAPI2 result lists into 1 list

    Combined list, emulates the output of a fused 'Warehouse' data source.

    >>> result1 = [('a','b'),(2.0,'30'),(2.1,'35')]
    >>> result2 = [('z',),('1999-01-01T00:00:00Z',)]
    >>> dict_results = {'project.s1':result1, 'project.s2':result2}
    >>> combined = get_source_results_combined( dict_results)
    >>> len(combined) #Expect header row + 3 data row
    4
    >>> header_combined = combined[0]
    >>> len(header_combined) #Expect 3 fields in the header 
    3
    >>> field_expected_1 = 'project.s1'+util.str_source_variable_separator+'a'
    >>> field_expected_1 in header_combined
    True
    >>> f_expect2 = 'project.s1'+util.str_source_variable_separator+'b'
    >>> f_expect3 = 'project.s2'+util.str_source_variable_separator+'z'
    >>> all([f_expect3 in header_combined, f_expect2 in header_combined])
    True
    >>> result3 = [('big','set')] #Try adding a large result set
    >>> result3.extend([(3.141,'2999-12-31T23:59:59Z') for i in range(9990000)])
    >>> dict_results['project2.big_set'] = result3
    >>> combined = get_source_results_combined( dict_results)
    >>> len(combined) #Expect header row + 9990003 data row
    9990004
    """
    # Combine resultsets
    # FIXME: Below may be possible with SQLalchemy ORM, but either way
    # Warehouse db schema is expected to obviate the need for this function.
    header_row_combined = []
    data_rows_combined = numpy.array([], dtype=object)#conserve memory w/ NumPy
    for str_source_id in dict_results_by_id.keys():
        #1) Add columns from this resultset to header row
        #No dataset fields have been identified as compatible/shared dimensions
        #.. so we make no attempt to combine/consolidate them.
        result = dict_results_by_id[ str_source_id]
        if result is None:
            continue #No results Skipping.
        try:
            header_result = result[0]
            header_prefixed = []
            for str_field in header_result:
                str_field_prefixed =util.prefix_field_name(str_field, str_source_id)
                header_prefixed.append( str_field_prefixed)
            header_row_combined.extend( header_prefixed)
        except IndexError:
            #source resultset has no header! Skipping.
            continue
        #2) Extend all combined data rows w/ null values for the new header fields
        int_starting_combined_width = 0
        if len(data_rows_combined) > 0:
            int_rows, int_starting_combined_width = data_rows_combined.shape
            int_header_len = len(header_result)
            tuple_col_padding_size = (int_rows, int_header_len)
            array_padding = numpy.empty(tuple_col_padding_size, dtype=object)
            array_padding.fill(str_no_data_placeholder)
            list_add_columns = [data_rows_combined, array_padding]
            data_rows_combined = numpy.column_stack(list_add_columns)
        #3) Add rows from this resultset to combined data rows
        array_result_data_rows = numpy.array(result[1:], dtype=object)
        if int_starting_combined_width > 0:
            # extend the new data rows with additional columns of padding
            int_pad_width = int_starting_combined_width#offset new fields
            int_padding_rows = len(array_result_data_rows)
            tuple_padding_size = (int_padding_rows, int_pad_width)
            array_padding_new_rows = numpy.empty(tuple_padding_size, dtype=object)
            array_padding_new_rows.fill(str_no_data_placeholder)
            list_add_columns = [array_padding_new_rows, array_result_data_rows]
            array_result_data_rows = numpy.column_stack(list_add_columns)
        if int_starting_combined_width == 0:
            data_rows_combined = array_result_data_rows
            continue
        #Otherwise,now that new rows size is same as master list: append
        list_add_new_rows = [data_rows_combined, array_result_data_rows]
        data_rows_combined = numpy.concatenate( list_add_new_rows)
    # convert header list, plus list of data-row lists
    # into one list of tuples
    result_combined = []
    result_combined.append( tuple(header_row_combined) )
    for list_data_row in data_rows_combined:
        result_combined.append( tuple(list_data_row) )
    return result_combined

def get_list_of_warehouse_variables():
    """
    Returns a list of names, representing all available Warehouse variables
    """
    list_variables = []
    loader = api.config_loader
    for dict_source in loader.get_list_of_etl_dicts():
        str_dataset_id = dict_source['id']
        # retrieve & decode the configured list of fields+types
        str_field_types_json = dict_source['python_types']
        dict_field_types = json.loads( str_field_types_json)
        # add the field names, to our list
        for str_source_variable in dict_field_types.keys():
            str_warehouse_variable = util.prefix_field_name(str_source_variable, str_dataset_id)
            list_variables.append( str_warehouse_variable)
    return list_variables

def get_source_tables():
    """
    Returns list of 'table' warehouse support DTOs representing all configured
    data sources.
    """
    with get_source_model_session() as available_model:
        return available_model['tables']

def get_source_variables():
    """
    Returns 'variable' DWSupport objects representing all configured fields
    """
    with get_source_model_session() as available_model:
        return available_model['variables']

@contextlib.contextmanager
def get_source_model_session():
    """
    returns a dict, representing the complete DWSupport configuration

    """
    yield prefetch_cache.get_model()

def get_sql_filtered(source_table, python_types, filters
                     ,empty_fact_dimensions = []):
    """
    Returns String,representing an inline view definition for retrieving source

    Keyword Parameters:
    source_table  -- a 'table' warehouse support DTO,representing the source
      returned SQL will retrieve.
    python_types  -- JSON encoded string representing a Dict that maps
      field names to Python type constructors
    filters  -- list of Strings, representing Selection filter expressions
    empty_cell_dimensions  -- list of Strings representing Dimension
       tables (or OLAP-Roles) which are to be OUTER JOINED to produce
       empty Fact value cells for all Dimensional values not found in
       the fact.

    TODO: provide unittest coverage
    """
    try:
        table_type.validate( source_table['type'])
    except table_type.ValidateUnexpectedValue as e:
        raise NotImplementedError('No SQL Generation method, for type: {}'.format(source_table)) from e #TODO: make this into a local class
    schema = "dw" #Default, for now all warehoused tables are in same schema
    #if source is a Fact table, join on its dimensions & alias all dimensional fields
    with get_source_model_session() as current_model:
        if source_table['type'] == 'fact':
            # compose sql:
            fact_name = source_table['name']
            # get variable lists & associations, by parent table_name
            variables, associations_by_parent, aliases, nonselects = get_fact_children(fact_name, current_model)
            return sqlgenerator.get_fact_sql(fact_name, schema, variables
                                             ,associations_by_parent, aliases, current_model
                                             ,nonselects, filters, empty_fact_dimensions)
        #source is a Dimension or OLAP-Role
        # get dimension fields
        dimension_name = source_table['name']
        associations = current_model['associations']
        if source_table['type'] == 'dimension role':
            role_name = source_table['name'] #Name is actually an alias
            # locate base dimension name
            dimension_name = _get_alias_base( role_name, associations)
        variables = variable.get(dimension_name, connection_func=util.get_dwsupport_connection)
        if source_table['type'] == 'dimension role':
            variables = _get_aliased_variables(role_name, variables)
        # compose SQL
        return _get_dim_sql(dimension_name, schema, variables, python_types, current_model, filters)

def get_fact_children(fact_name, current_model):
    """
    Returns Fact table variables, associations, OLAP-roles & role-support Dims

    Variables & associations a represented as Dicts, indexed by parent
    table_name. Dimension roles are returned as a list of names.

    Keyword Parameters:
    fact_name  -- String, representing name of the fact table for which dicts
        of variable lists and associations are to be retrieved.
    current_model  -- Dict, representing the full DWSupport configuration
    """
    # get associations, by parent table_name
    associations_all = current_model['associations']
    associations_by_parent = {}
    aliases = []
    nonselect_tables = []
    for a in associations_all:
        if a['table'] == fact_name:
            # add association to Dict,only if it relates to fact_name
            dimension_name = a['parent']
            associations_by_parent[ dimension_name] = a
            if a['type'] == 'fact dimension role':
                # Make a note, if the Dict is an alias("Role")
                aliases.append( dimension_name)
    # construct artificial Dimension relations,for any standalone OLAP-Roles
    for table_name in aliases:
        #fetch the Role information
        role_association = associations_by_parent[table_name]
        role_name = role_association['parent']
        dimension_name = _get_alias_base( role_name, associations_all)
        # check if base dimension is listed
        if dimension_name not in associations_by_parent.keys():
            # build a fake association, for the dimension
            fake_base_association = dict(role_association)
            fake_base_association['parent'] = dimension_name
            fake_base_association['type'] = 'fact dimension'
            # map artificial relation, to enable SQL generation
            associations_by_parent[ dimension_name] = fake_base_association
            nonselect_tables.append( dimension_name) #mark as artificial
    # get variables, by table_name
    relevant_tables = [fact_name] + list(associations_by_parent.keys())
    variables_all = current_model['variables']
    variables_by_parent = {}
    variables_by_table_name = {} #also, prepare a map of variables
    for v in variables_all:
        table_name = v['table']
        variables_by_table_name.setdefault(table_name, [])#map is for Aliases
        variables_by_table_name[table_name].append(v)
        if table_name in relevant_tables:
            # add variable to our Dict lists, if it relates to this source
            variables_by_parent.setdefault(table_name, [])#if new table,init our Dict
            variables_by_parent[table_name].append(v)
    # get variables for aliases (Aliases dont have their own variables)
    # also, construct artificial Fact-to-dim associations for aliases.
    for table_name in aliases:
        role_association = associations_by_parent[table_name]
        role_name = role_association['parent']
        dimension_name = _get_alias_base( role_name, associations_all)
        dimension_variables = variables_by_table_name[dimension_name]
        alias_variables = _get_aliased_variables( role_name
                                                 ,dimension_variables)
        variables_by_parent[table_name] = alias_variables
        # replace "role" association with an 'aliased' fact association
        aliased_association = dict(role_association)
        aliased_association['parent'] = dimension_name
        associations_by_parent[table_name] = aliased_association
    return variables_by_parent, associations_by_parent, aliases, nonselect_tables

def get_fact_variables(fact_table, current_model):
    """
    Returns Dicts,representing fact's variable dtos & physical columns

    Both dicts are indexed by variable's web API identifier (e.g.:
    'fact_column_name', 'associated_dimension$dim_column_name', or
    'custom_variable_identifier')

    Keyword Parameters:
    fact_table  -- dwsupport DTO,representing the fact table for which Dict of
        python types is to be retreived.
    current_model  -- Dict, representing the full DWSupport configuration

    TODO: improve test coverage
    """
    fact_name = fact_table['name']
    variables, associations_garbage, alias_garbage, nonselect_tables = get_fact_children(fact_name, current_model)
    fact_variables = {}
    physical_columns ={}
    for table_name in variables:
        #retrieve variables list for all selectable Fact fields
        if table_name in nonselect_tables:
            continue # skip
        variable_list = variables[table_name]
        for var in variable_list:
            final_var = dict(var)
            variable_id = _get_fact_variable_name(var, fact_name)
            final_var['column'] = variable_id
            custom_id = util.get_custom_variable_name(
                 final_var
                ,current_model)
            if custom_id is not None:
                variable_id = custom_id
                final_var['column'] = custom_id
            fact_variables[variable_id] = final_var
            physical_columns[variable_id] = var['column']
    return fact_variables, physical_columns

def _get_fact_variable_name( source_variable, fact_name):
    """
    Utility function,returning API identifier for the referenced variable

    Keyword Parameters:
    source_variable  -- dwsupport DTO, representing a dimension or fact summary
        field.
    fact_name  -- String, representing the name of the fact table fields are
        associated with.

    >>> fact_var1 = {'column':'measured_kg','title': 'Measured Fact1','table':'foo_fact'}
    >>> _get_fact_variable_name( fact_var1, 'foo_fact')
    'measured_kg'
    >>> dim_var1 = {'column':'date','title': 'Trip Date','table':'date_dim'}
    >>> _get_fact_variable_name( dim_var1, 'foo_fact')
    'date_dim$date'
    """
    identifier = source_variable['column'] #initialize 
    variable_table = source_variable['table']
    if not variable_table == fact_name: #variable did not come from the Fact
        # table. Prefix with the name of it's originating table,to orient user
        identifier = util.prefix_field_name( identifier, variable_table)
    return identifier

def _get_dim_sql( dimension_name, schema, variables, python_types, model, filters):
    """
    Utility function, to generate SQL select statement for a single dimension

    Keyword Parameters:
    dimension_name  -- String representation of the dimension table name
    schema  --  String representation of db schema where dimension is located
    variables  --  list of 'variable' warehouse support DTOs
    python_types  -- JSON encoded string representing a Dict that maps
      field names to Python type constructors
    model  -- dictionary of lists, representing warehouse configuration
      model.
    filters  -- list of Strings, representing Selection filter expressions

    >>> var1 = { 'id': 1, 'column':'bar_ml', 'title':'bar'\
                ,'python_type': 'float' \
                ,'table': 'foo_dim'}
    >>> var2 = { 'id': 2, 'column':'baz_kg', 'title':'baz'\
                ,'python_type': 'float' \
                ,'table': 'foo_dim'}
    >>> vars = [var1, var2]
    >>> python_types = '{"bar_ml":"int", "baz_kg":"float"}'
    >>> model_no_custom_ids = {'variable_custom_identifiers': []}
    >>> sql, binds = _get_dim_sql( 'foo_dim', 'proj1', vars, python_types, model_no_custom_ids, [])
    >>> sql
    'SELECT bar_ml, baz_kg \\nFROM proj1.foo_dim'
    >>> binds
    {}
    >>> filters = ['bar_ml<9']
    >>> sql, binds = _get_dim_sql( 'foo_dim', 'proj1', vars, python_types, model_no_custom_ids, filters)
    >>> sql
    'SELECT bar_ml, baz_kg \\nFROM proj1.foo_dim \\nWHERE foo_dim.bar_ml < %(0)s'
    >>> binds
    {'0': 9}
    >>> model_custom_ids = {'variable_custom_identifiers': [
    ...                         { 'table': 'foo_dim'
    ...                          ,'column': 'baz_kg'
    ...                          ,'id': 'baz'}]}
    >>> filters = ['baz>12']
    >>> python_types = '{"bar_ml":"int", "baz":"float"}'
    >>> sql, binds = _get_dim_sql( 'foo_dim', 'proj1', vars, python_types, model_custom_ids, filters)
    >>> sql
    'SELECT bar_ml, baz_kg AS baz \\nFROM proj1.foo_dim \\nWHERE foo_dim.baz_kg > %(0)s'
    >>> binds
    {'0': 12.0}
    """
    columns = []
    # compose SQL column definitions, for us to select
    for dimension_variable in variables:
        field_name = dimension_variable['column']
        column = sql.column(field_name)
        custom_id = util.get_custom_variable_name(
            dimension_variable
            ,model)
        if custom_id is not None:
            column = column.label(custom_id)
        columns.append( column)
    metadata_garbage = sql.MetaData()#the md workspace is manditory & useless
    table_with_schema = sql.Table( dimension_name, metadata_garbage
                                  ,schema=schema)
    statement = sql.select( columns).select_from(table_with_schema)
    # append filtering access conditions
    filtered_statement = statement
    binds = {}
    columns_by_name = {} #build map of columns, for fast access
    for column in columns:
        columns_by_name[str(column)] = column
    for filter_urlencoded in filters:
        start_bind = len(binds)
        #TODO: refactor with similar sqlgenerator._get_sqlalchemy_statement_filtered code
        filter_tuple = parameters.get_filter_condition_sqlalchemy_pgsql_string(
            python_types
            ,filter_urlencoded
            ,start_bind)
        filter_expression, filter_binds = filter_tuple
        binds.update(filter_binds)
        # replace web field name with 'schema.table.column'
        #TODO: refactor similar sqlgenerator._get_types_and_variable_table_pairs code
        types_and_variable_table_tuple = sqlgenerator._get_types_and_variable_table_pairs(
            dimension_name
            ,{dimension_name: variables}
            ,model
        )
        garbage_python_types, variables_and_tables_by_web_name = types_and_variable_table_tuple
        web_field = parameters.get_filter_processed_3tuple(python_types, filter_urlencoded)[0]
        var, table_name = variables_and_tables_by_web_name[web_field]
        join_column = '.'.join([table_name, var['column']])
        clean_expression = filter_expression.lstrip()#parameters starts w/: ' '
        rewritten_expression = clean_expression.replace(web_field, join_column)
        sa_text = sql.text(rewritten_expression)
        filtered_statement = filtered_statement.where(sa_text)#append condition
    postgresql_statement = filtered_statement.compile(dialect=postgresql.dialect())
    string_sql = str(postgresql_statement)
    return string_sql, binds

def get_variables(source_table):
    """
    Returns Dict,representing source fields mapped to DWSupport vars

    Keyword Parameters:
    source_table  -- a 'table' warehouse support DTO,representing the source
      for which Python types are to be returned.
    """
    table_name = source_table['name']
    with get_source_model_session() as current_model:
        all_variables = current_model['variables']
        table_variables = list()
        for variable in all_variables:
            if variable['table']==table_name:
                web_name = variable['column']
                # override the variable ID, if DWSupport specifies a custom ID
                custom_web_name = util.get_custom_variable_name(variable, current_model)
                if custom_web_name is not None: #TODO: refactor, to reduce code duplication
                    web_name = custom_web_name
                variable['column'] = web_name
                table_variables.append(variable)
    return _variable_map_by_name(table_variables)

def get_role_variables(source_table):
    """
    Returns Dict,representing source fields mapped to DWSupport vars

    Keyword Parameters:
    source_table  -- a 'table' warehouse support DTO,representing the
      source OLAP Dimension "Role" (Dimension alias) for which Python
      types are to be returned.
    """
    role_name = source_table['name']
    with get_source_model_session() as current_model:
        associations = current_model['associations']
        base_dimension_name = _get_alias_base( role_name, associations)
        dimension_variables = variable.get( base_dimension_name
                                           ,connection_func=util.get_dwsupport_connection)
        alias_variables = _get_aliased_variables( role_name
                                                 ,dimension_variables)
        for i,role_variable in enumerate(alias_variables):
            web_name = role_variable['column']
            # override the variable ID, if DWSupport specifies a custom ID
            custom_web_name = util.get_custom_variable_name(role_variable, current_model)
            if custom_web_name is not None: #TODO: refactor, to reduce code duplication
                web_name = custom_web_name
            role_variable['column'] = web_name
            alias_variables[i] = role_variable
    return _variable_map_by_name(alias_variables)

def _variable_map_by_name(variables):
    """
    Returns Dict,representing referenced variable fields mapped by name.

    Keyword Parameters:
    variables  -- list of 'variable_python_type' Warehouse support DTOs

    >>> from pprint import pprint
    >>> var1 = { 'column':'frob_hz', 'title':'Frobniz Resonance (Hz)'
    ...         ,'python_type': 'float'
    ...         ,'table': 'foo_fact'}
    >>> list1 = [var1]
    >>> pprint(_variable_map_by_name(list1))
    {'frob_hz': {'column': 'frob_hz',
                 'python_type': 'float',
                 'table': 'foo_fact',
                 'title': 'Frobniz Resonance (Hz)'}}
    """
    variable_by_field = {}
    for var in variables:
        field_name = var['column']
        variable_by_field[field_name] = var
    return variable_by_field

def _get_aliased_variables( role_name, dimension_variables):
    """
    Returns list of variable DTOs for a virtual/aliased Dimension "Role"

    Keyword Parameters:
    role_name  -- String, representing name of the OLAP dimension alias
      (Role) for which variables are to be returned.
    dimension_variables  -- list of 'variable' dto,representing the
      fields associated with the base Dimension which Role is an alias
      to.

    >>> from pprint import pprint
    >>> role_name = 'tuesdays_foo_dim'
    >>> var1 = { 'id': 1, 'column':'flavor', 'title':'Widget flavor'
    ...         ,'python_type': 'float', 'table': 'foo_dim'}
    >>> var2 = { 'id': 2, 'column':'brand', 'title':'Widget brand'
    ...         ,'python_type': 'str', 'table': 'foo_dim'}
    >>> aliased = _get_aliased_variables( role_name, [var1, var2])
    >>> pprint( aliased)
    [{'column': 'flavor',
      'id': 1,
      'python_type': 'float',
      'table': 'tuesdays_foo_dim',
      'title': 'Widget flavor'},
     {'column': 'brand',
      'id': 2,
      'python_type': 'str',
      'table': 'tuesdays_foo_dim',
      'title': 'Widget brand'}]
    """
    aliased_variables = []
    for dimension_variable in dimension_variables:
        new_variable = dict(dimension_variable)
        new_variable['table'] = role_name
        aliased_variables.append( new_variable)
    return aliased_variables

def _get_alias_base( role_name, associations):
    """
    Returns name of the Dimension, a OLAP-Role is based on
    Keyword Parameters:
    role_name  -- String, representing the name of an OLAP Role (Dimension
      alias).
    associations  -- List of dwsupport 'association' DTOs,representing
      *all* table_relations in the Warehouse support schema.

    >>> assoc1 = { 'table': 'sandwich_time_dim'
    ...           ,'parent': 'time_dim'
    ...           ,'type': 'dimension role base'}
    >>> _get_alias_base( 'sandwich_time_dim', [assoc1])
    'time_dim'
    """
    for table_association in associations:
        association_type = table_association['type']
        association_role_name = table_association['table']
        if ( (association_role_name == role_name)
                and (association_type == 'dimension role base') ):
            base_dimension_name = table_association['parent']
            break
    else:
        msg = "Unable to find dimensional alias for source: {}"
        raise Exception(msg.format(role_name)) #FIXME: pick a reasonable exception
    return base_dimension_name
