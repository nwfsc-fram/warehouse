"""
HTTP query string parameter-parsing features for 'Selection' RESTful resource

Copyright (C) 2015-2017 ERT Inc.
"""
import falcon
import urllib.parse
import collections
import datetime
import dateutil.parser
import re
import api.json as json
import pydoc
import pyparsing

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

class ReservedParameterNames:
    """
    Object defining all of the reserved URL query parameters (those assigned to
    specific Selection resource features/capabilities.
    """
    filters   = 'filters'
    variables = 'variables'
    datasets  = 'datasets'
    defaults = 'defaults'
    pivot_columns = 'pivot_columns'
    empty_cells = 'empty_cells'

    @classmethod
    def get_all( self):
        list_all_query_params = [
             self.filters
            ,self.variables
            ,self.datasets
            ,self.defaults
            ,self.pivot_columns
            ,self.empty_cells
        ]
        return list_all_query_params

class FilterVariableError(ValueError):
    """
    Exception raised when URL query 'filters' reference an unknown variable
    """
    pass

class FilterValueError(TypeError):
    """
    Exception raised when URL query 'filters' includes a unrecognized data value
    """
    pass

class PivotVariableError(ValueError):
    """
    Raised when URL 'pivot_columns' param used on a Dimensional data set
    """
    pass

class EmptyCellsSourceError(ValueError):
    """
    Raised when 'empty_cells' URL param used on a Dimensional data set
    """
    pass

class EmptyCellsDimensionError(ValueError):
    """
    empty_cells' URL param value, not recognized as a source dimension
    """
    pass

class SourceTypeError(TypeError):
    """
    Exception raised when data field's referenced Python type is unrecognized
    """
    pass

def get_list_requested_parameter( str_parameter, request):
    """
    Extracts list of values for requested parameter, from query string

    Keyword parameters:
    str_parameter -- String, representing the parameter to extract
    request -- Falcon request

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'variables=var1'
    >>> get_list_requested_parameter( 'variables', tr.req)
    ['var1']
    >>> tr.req.query_string = 'variabRfles=var1'
    >>> get_list_requested_parameter( 'variables', tr.req)
    []
    >>> tr.req.query_string = 'variables=v1,v2'
    >>> get_list_requested_parameter( 'variables', tr.req)
    ['v1', 'v2']
    >>> tr.req.query_string = 'variables=v1&variables=v2'
    >>> get_list_requested_parameter( 'variables', tr.req)
    ['v1', 'v2']
    """
    bool_use_empty_string_for_empty_field_values = True #falcon parameter
    list_empty = [] #Empty list means: Assume all variables are desired
    dict_query_string = falcon.util.uri.parse_query_string(
                              request.query_string
                            , bool_use_empty_string_for_empty_field_values)
    try:
        obj_value = dict_query_string[ str_parameter]
        if isinstance(obj_value, list):
            return obj_value
        elif obj_value == '':
            return list_empty #if requested variable is empty,return empty list
        return [obj_value] #if only 1 variable was requested,Wrap val in a list
    except KeyError:
        return list_empty

def get_requested_variables( request):
    """
    Extracts the requested dataset fields/variables from query string

    Keyword parameters:
    request -- Falcon request

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'variables=var1'
    >>> get_requested_variables( tr.req)
    ['var1']
    >>> tr.req.query_string = 'variabRfles=var1'
    >>> get_requested_variables( tr.req)
    []
    >>> tr.req.query_string = 'variables=v1,v2'
    >>> get_requested_variables( tr.req)
    ['v1', 'v2']
    >>> tr.req.query_string = 'variables=v1&variables=v2'
    >>> get_requested_variables( tr.req)
    ['v1', 'v2']
    """
    return get_list_requested_parameter(ReservedParameterNames.variables, request)

def get_requested_filters( request):
    """
    Extracts all requested dataset filters from the URL query string.

    Keyword parameters:
    request -- Falcon request

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'variables=var1&filters=var2=42&var3=9'
    >>> get_requested_filters( tr.req)
    ['var2=42', 'var3=9']
    """
    filters = get_requested_filters_explicit( request)
    filters.extend( get_requested_filters_implicit( request))
    return filters

def get_requested_filters_explicit( request):
    """
    Extracts the requested dataset filters, from the dedicated URL query
    string parameter for filters.

    Keyword parameters:
    request -- Falcon request

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'variables=var1&filters=var2=42'
    >>> get_requested_filters_explicit( tr.req)
    ['var2=42']
    >>> tr.req.query_string = 'variables=var1&filFrs=var2=42'
    >>> get_requested_filters_explicit( tr.req)
    []
    >>> tr.req.query_string = 'filters=var2=42,var3=9'
    >>> get_requested_filters_explicit( tr.req)
    ['var2=42', 'var3=9']
    >>> tr.req.query_string = 'variables=v1&filters=var2=42&filters=var3=9'
    >>> get_requested_filters_explicit( tr.req)
    ['var2=42', 'var3=9']
    """
    return get_list_requested_parameter(ReservedParameterNames.filters, request)

def get_requested_filters_implicit( request):
    """
    Extracts the requested dataset equality filters, specified directly in the
    URL query string.

    Keyword parameters:
    request -- Falcon request

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'variables=var1&var2=42'
    >>> get_requested_filters_implicit( tr.req)
    ['var2=42']
    >>> tr.req.query_string = 'variables=var1&filters=var2=42'
    >>> get_requested_filters_implicit( tr.req)
    []
    >>> tr.req.query_string = ''
    >>> get_requested_filters_implicit( tr.req)
    []
    >>> tr.req.query_string = 'var2=42&var3=9'
    >>> l = get_requested_filters_implicit( tr.req)
    >>> l.sort() # filter order isnt stable; sort, for testing
    >>> l
    ['var2=42', 'var3=9']
    >>> tr.req.query_string = 'variables=v1&var2=42&var3=9'
    >>> l = get_requested_filters_implicit( tr.req)
    >>> l.sort() # filter order isnt stable; sort, for testing
    >>> l
    ['var2=42', 'var3=9']
    >>> tr.req.query_string = 'var2=42&var2=9'
    >>> l = get_requested_filters_implicit( tr.req)
    >>> l
    ['var2|=["42", "9"]']
    """
    bool_use_empty_string_for_empty_field_values = True #falcon parameter
    dict_query_string = falcon.util.uri.parse_query_string(
                              request.query_string
                            , bool_use_empty_string_for_empty_field_values)
    # get all candidate filter params (query params, without defined functions)
    candidate_filter_keys = []
    for key in dict_query_string.keys():
        if key == '':
            continue #skip any empty key.
        if key not in ReservedParameterNames.get_all():
                candidate_filter_keys.append( key)
    # construct a list of filter strings
    filter_strings = []
    for key in candidate_filter_keys:
        #TODO: check if key is a valid field name
        parameter_value = dict_query_string[ key]
        # translate multiple values, into an 'OR' filter string
        if isinstance( parameter_value, list):
            #Falcon has converted multiple parameter values into a list
            parameter_value.sort() #sort strings('88'<'9')to make things pretty
            json_value = json.dumps(parameter_value)
            new_filter_string = '{}|={}'.format(key, json_value)
            filter_strings.append( new_filter_string)
            continue
        # translate single parameter values, into a single equality filter.
        if isinstance( parameter_value, str):
            new_filter_string = '{}={}'.format(key, parameter_value)
            filter_strings.append( new_filter_string)
            continue
    return filter_strings

def get_requested_pivot_columns(request, source_id, dwsupport_tables):
    """
    Extracts the requested pivot fields/variables from query string

    Keyword parameters:
    request -- Falcon request
    source_id  -- String, representing dataset API id requested
    dwsupport_tables  -- list of 'table' support DTOs defining type
      (dimension, fact, etc.) of the data sources

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'pivot_columns=test_dim$my_pivot_field1'
    >>> source = 'my.source1'
    >>> tables = [{'name': 'source1','type':'fact'}]
    >>> get_requested_pivot_columns(tr.req, source, tables)
    ['test_dim$my_pivot_field1']
    >>> bad_source = 'my.test_dim' #cannot pivot on a Dimension (yet)
    >>> get_requested_pivot_columns(tr.req, bad_source, tables)
    Traceback (most recent call last):
       ...
    api.resources.source.selection.parameters.PivotVariableError: Pivot not available for source: my.test_dim
    >>> tr.req.query_string = 'on_coluDGOmns=var1'
    >>> get_requested_pivot_columns(tr.req, source, tables)
    []
    >>> tr.req.query_string = 'pivot_columns=great_dim$var1,great_dim$var2'
    >>> get_requested_pivot_columns(tr.req, source, tables)
    ['great_dim$var1', 'great_dim$var2']
    >>> tr.req.query_string = 'pivot_columns=great_dim$var1&pivot_columns=other_dim$var1'
    >>> get_requested_pivot_columns(tr.req, source, tables)
    ['great_dim$var1', 'other_dim$var1']
    """
    pivot_columns = get_list_requested_parameter(
        ReservedParameterNames.pivot_columns
        ,request)
    if not pivot_columns: #empty, or not present
        return []
    #check if pivot is valid, for this source
    project_name, source_name = source_id.split('.')
    for table in dwsupport_tables:
        if (table['name'] == source_name #assume no 2 projects have same source
                and table['type'] == 'fact'):
            return pivot_columns
    raise PivotVariableError('Pivot not available for source: '+source_id)

def get_requested_empty_cells(request, source_id, dwsupport_tables
                              ,dwsupport_associations):
    """
    Extracts the requested EMPTY cell Dimension names from query string

    Keyword parameters:
    request -- Falcon request
    source_id  -- String, representing dataset API id requested
    dwsupport_tables  -- list of 'table' support DTOs defining type
      (dimension, fact, etc.) of the data sources
    dwsupport_associations  -- list of 'association' support DTOs
      defining relationships between Warehouse tables.

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'empty_cells=test_dim'
    >>> source = 'my.source1'
    >>> tables = [ {'name': 'source1', 'type': 'fact'}
    ...           ,{'name': 'test_dim', 'type': 'dimension'}]
    >>> assocs = [{ 'table': 'source1', 'parent': 'test_dim'
    ...            ,'type': 'fact dimension'}]
    >>> get_requested_empty_cells(tr.req, source, tables, assocs)
    ['test_dim']
    >>> bad_source = 'my.test_dim' #Dim source EMPTY cells never exist
    >>> get_requested_empty_cells(tr.req, bad_source, tables, assocs)
    Traceback (most recent call last):
       ...
    api.resources.source.selection.parameters.EmptyCellsSourceError: cannot use parameter on Dimensional source (my.test_dim).
    >>> tr.req.query_string = 'empty_cells=unknown_dim' #not associated with source
    >>> get_requested_empty_cells(tr.req, source, tables, assocs)
    Traceback (most recent call last):
       ...
    api.resources.source.selection.parameters.EmptyCellsDimensionError: not a valid source Dimension: unknown_dim
    >>> tr.req.query_string = 'empt(SDFGy_cells=var1'
    >>> get_requested_empty_cells(tr.req, source, tables, assocs)
    []
    >>> tables = [ {'name': 'source1', 'type': 'fact'}
    ...           ,{'name': 'great_dim', 'type': 'dimension'}
    ...           ,{'name': 'other_dim', 'type': 'dimension'}
    ...           ,{'name': 'another_dim', 'type': 'dimension role'}]
    >>> assocs = [ { 'table': 'source1', 'parent': 'great_dim'
    ...             ,'type': 'fact dimension'}
    ...           ,{ 'table': 'source1', 'parent': 'other_dim'
    ...             ,'type': 'fact dimension'}
    ...           ,{ 'table': 'source1', 'parent': 'another_dim'
    ...             ,'type': 'fact dimension role'}]
    >>> tr.req.query_string = 'empty_cells=great_dim,another_dim'
    >>> get_requested_empty_cells(tr.req, source, tables, assocs)
    ['great_dim', 'another_dim']
    >>> tr.req.query_string = 'empty_cells=great_dim&empty_cells=other_dim'
    >>> get_requested_empty_cells(tr.req, source, tables, assocs)
    ['great_dim', 'other_dim']
    """
    empty_cells = get_list_requested_parameter(
        ReservedParameterNames.empty_cells
        ,request)
    if not empty_cells: #empty, or not present
        return []
    #check if pivot is valid, for this source
    project_name, source_name = source_id.split('.')
    for table in dwsupport_tables:
        if (table['name'] == source_name #assume no 2 projects have same source
                and table['type'] != 'fact'):
            msg = 'cannot use parameter on Dimensional source ({}).'
            raise EmptyCellsSourceError(msg.format(source_id))
    #check if values refer to valid source Dimensions
    source_association_names = [] #valid Dimension names, for source
    for relation in dwsupport_associations:
        if (relation['table'] == source_name
                and relation['type'] in ['fact dimension','fact dimension role']):
            dimensional_table_name = relation['parent']
            source_association_names.append(dimensional_table_name)
    for identifier in empty_cells:
        if identifier not in source_association_names:
            msg = 'not a valid source Dimension: {}'.format(identifier)
            raise EmptyCellsDimensionError(msg)
    return empty_cells

def parse_plus_string_to_list( plus_delimited_string):
    """
    utility function to convert '+' delimited, quoted string into list of
    substrings.

    >>> s1 = "a"
    >>> parse_plus_string_to_list( s1)
    ['a']
    >>> s1 = "a+b"
    >>> parse_plus_string_to_list( s1)
    ['a', 'b']
    """
    delimiter = '+'
    non_delimiter_chars = pyparsing.printables.replace(delimiter,'')
    OneOrMore = pyparsing.OneOrMore
    expression = pyparsing.originalTextFor(
        OneOrMore( pyparsing.quotedString | pyparsing.Word(non_delimiter_chars)
        )
    )
    expressions = pyparsing.delimitedList( expression, delimiter)
    parse_result = expressions.parseString( plus_delimited_string)
    # extract the identified tokens from the pyparsing object, as a list
    results = list( parse_result)
    return results

def get_requested_datasets( request):
    """
    Extracts from query string which dataset IDs output should be limited to

    Keyword parameters:
    request -- Falcon request

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> tr.req.query_string = 'variables=var1&datasets=Proj1'
    >>> get_requested_datasets( tr.req)
    ['Proj1']
    >>> tr.req.query_string = 'variables=var1&filFrs=Proj1'
    >>> get_requested_datasets( tr.req)
    []
    >>> tr.req.query_string = 'datasets=Proj1,Proj2'
    >>> get_requested_datasets( tr.req)
    ['Proj1', 'Proj2']
    >>> tr.req.query_string = 'variables=v1&datasets=Proj1&datasets=Proj42'
    >>> get_requested_datasets( tr.req)
    ['Proj1', 'Proj42']
    """
    return get_list_requested_parameter(ReservedParameterNames.datasets, request)

def get_index_caseinsensitive(str_value, list_unknown_case):
    list_lowercased = [value.lower() for value in list_unknown_case]
    if str_value.lower() in list_lowercased:
        return list_lowercased.index(str_value.lower())
    #else, not found - raise
    raise ValueError

def get_result_subset(result_generator, variables=[]):
    """
    Return generator of DBAPI tuples(& prefixed header row) subsetted by header value

    Keyword Parameters:
    result_generator  -- generator of DBAPI tuples (& prefixed header row)
      representing unsubsetted results from the Warehouse
    variables  -- list of headers to be retained, in the subset. If
      list is empty then all fields will be retained

    >>> def test_generator1():
    ...     yield ('a', 'b', 'z')
    >>> gen = get_result_subset(test_generator1(), [])
    >>> next(gen)
    ('a', 'b', 'z')
    >>> gen = get_result_subset(test_generator1(), ['b','a'])
    >>> next(gen)
    ('a', 'b')
    >>> def test_generator2():
    ...     yield ('a', 'b', 'z')
    ...     yield (1, 3, 7)
    >>> gen = get_result_subset(test_generator2(), ['z'])
    >>> next(gen)
    ('z',)
    >>> next(gen)
    (7,)
    """
    #fetch header row & process, before processing remaining result rows
    tuple_header = next(result_generator)
    header_processed = False

    # identify which indexes are to be retained
    list_retain_indices = []
    try:
        tuple_header[0]
    except IndexError:
        yield tuple_header #empty list; return. (no subsetting possible)
        raise StopIteration() #end
    if not variables:
        #No variables specified... return all values
        if header_processed:
            for remaining in result_generator:
                yield remaining
        else:
            header_processed = True
            yield tuple_header
            for remaining in result_generator:
                yield remaining #end

    for variable in variables:
        # check if requested var is in header row of result (case insensitive)
        try:
            int_index = get_index_caseinsensitive(variable, tuple_header)
            list_retain_indices.append( int_index)
        except ValueError:
            pass # not found, skip
    # return retained indices, to their natural order
    list_retain_indices.sort()

    # construct new tuples, yielding only the desired indexes
    while True:
        if header_processed:
            tuple_row = next(result_generator)
        if not header_processed:
            tuple_row = tuple_header
            header_processed = True
        # add row values that are to be retained to a temporary list
        list_compose = []
        for index in list_retain_indices:
            list_compose.append( tuple_row[index])
        # convert temporary list, into a new (immutable) tuple
        yield tuple(list_compose)

class FilterParseError(Exception):
    """
    Thrown when a filter cannot be parsed.
    """
    pass

def get_sql_filtered( source_query, python_types, db_conf_file_name, filters=[]):
    """
    Return list of DBAPI tuples (& prefixed header row) filtered by value

    Keyword Parameters:
    source_query -- String, representing SQL definition of requested datasource
    python_types  -- JSON encoded string representing a Dict that maps
      field names to Python type constructors
    db_conf_file_name  --  String representing the server/ module .ini settings
      file, defining how to connect to the Source

    Exceptions:
    FilterVariableError -- filters variable not found in header

    >>> args1 = { 'source_query': "schema.InformativeView"
    ...        , 'python_types': '{"a":"str","b":"int","z":"float"}'
    ...        , 'db_conf_file_name': 'db_config.ini'
    ...        }
    >>> get_sql_filtered( filters=['z=7'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE z = %s', [7.0])
    >>> get_sql_filtered( filters=['a=77'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE a = %s', ['77'])
    >>> get_sql_filtered( filters=['a=77','z>=77'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE a = %s AND z >= %s', ['77', 77.0])
    >>> args1['db_conf_file_name'] = 'db_trawl.ini'
    >>> get_sql_filtered( filters=['z=7'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE z = :0', [7.0])
    >>> get_sql_filtered( filters=['a=77','z>=77'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE a = :0 AND z >= :1', ['77', 77.0])
    >>> get_sql_filtered( filters=['z~=7'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE REGEXP_LIKE(z, :0)', ['7'])
    >>> get_sql_filtered( filters=['a|=["5", "77"]'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE ( (a = :0) OR (a = :1) )', ['5', '77'])
    >>> get_sql_filtered( filters=['z|=["5", "77"]'], **args1)
    ('SELECT "raw".* FROM (schema.InformativeView) "raw" WHERE ( (z = :0) OR (z = :1) )', [5.0, 77.0])
    """
    # wrap source's table name, or inline view definition, with an outer select
    manditory_pgsql_alias = '"raw"'#PostgreSQL requires any name for inline view
    sql_outer_template = "SELECT {alias}.* FROM ({query}) {alias}"
    str_sql_outer = sql_outer_template.format( query=source_query
                                              ,alias=manditory_pgsql_alias)
    str_pgsql_conn = ['db_config.ini','db_dwsupport.ini']#FIXME:improve detection of SQL dialect
    # Append filter to end of the outer select, as conditional access clauses
    binds = []
    for str_filter_urlencoded in filters:
        str_access_clause = "WHERE"
        if len(binds) > 0:
            str_access_clause = "AND"
        bind_start = len(binds)
        if db_conf_file_name not in str_pgsql_conn:
            #use the Oracle regexp syntax
            access_condition, filter_binds =get_filter_condition_oracle_string(
                python_types
                ,str_filter_urlencoded
                ,bind_start)
        else:
            #TODO: why not use get_filter_condition_sqlalchemy_pgsql_string ?
            access_condition, filter_binds = get_filter_condition_pgsql_string(
                python_types
                ,str_filter_urlencoded
                ,bind_start)
        str_sql_outer += ' ' + str_access_clause + access_condition
        binds.extend(filter_binds)

    return str_sql_outer, binds

def get_filter_condition_oracle_string(python_types, filter_urlencoded, start_bind):
    """
    Convert HTTP filter to SQL expression(ora) +Python bind value(s)

    Keyword Parameters:
    python_types  -- JSON encoded string representing a Dict that maps
      field names to Python type constructors
    filter_urlencoded  -- String, representing the HTTP filter
    start_bind  -- Integer representing the starting numeral to use
      for SQL bind variable identifier.

    Exceptions:
    FilterVariableError -- filters variable not found in header

    >>> python_types = '{"a":"str","b":"int","z":"float"}'
    >>> get_filter_condition_oracle_string(python_types, 'z=7', 0)
    (' z = :0', [7.0])
    >>> get_filter_condition_oracle_string(python_types, 'a=77', 1)
    (' a = :1', ['77'])
    >>> get_filter_condition_oracle_string(python_types, 'z~=7', 0)
    (' REGEXP_LIKE(z, :0)', ['7'])
    >>> get_filter_condition_oracle_string(python_types, 'a|=["5", "77"]', 0)
    (' ( (a = :0) OR (a = :1) )', ['5', '77'])
    >>> get_filter_condition_oracle_string(python_types, 'z|=["5", "77"]', 0)
    (' ( (z = :0) OR (z = :1) )', [5.0, 77.0])
    """
    field, operator, obj_bind_val = get_filter_processed_3tuple(python_types, filter_urlencoded)
    #for now, bind target will just be sequential integer (likely started from 0)
    bind_target = str(start_bind)
    sql_equality_statement = '({} = :{})' #default, oracle syntax
    sql_simple_access_predicate = " {} {} :{}"
    sql_regexp_access_predicate = " REGEXP_LIKE({field}, :{bind})"

    if operator == '~=':
        format_arguments = {'field' : field
                           ,'bind'  : bind_target
                           }
        sql = sql_regexp_access_predicate.format( **format_arguments)
        return sql, [obj_bind_val]
    if operator == '|=':
        binds = []
        or_statements = [] # construct a set of ( () OR () ... ) equality expressions
        for bind_val in obj_bind_val:
            equality_statement = sql_equality_statement.format(field, bind_target)
            or_statements.append( equality_statement)
            # add the values, into the binds list
            binds.append( bind_val)
            bind_target = str(start_bind + len(binds)) #increment label
        # now connect the set of expressions, with 'OR's
        or_clauses = " OR ".join(or_statements)
        # ... and append equality expression string-representation, to the current query
        access_clause = " ( {} )".format(or_clauses)
        return access_clause, binds
    #Else, just compose a simple access predicate
    access_clause = sql_simple_access_predicate.format(field
                                                       ,operator
                                                       ,bind_target)
    return access_clause, [obj_bind_val]

def get_filter_condition_pgsql_string(python_types, filter_urlencoded, start_bind):
    """
    Convert HTTP filter to SQL expression(pgsql)+bind value(s) list

    TODO: should get_filter_condition_sqlalchemy_pgsql_string replace this function?

    Keyword Parameters:
    python_types  -- JSON encoded string representing a Dict that maps
      field names to Python type constructors
    filter_urlencoded  -- String, representing the HTTP filter
    start_bind  -- Integer representing the starting numeral to use
      for SQL bind variable identifier.

    Exceptions:
    FilterVariableError -- filters variable not found in header

    >>> python_types = '{"a":"str","b":"int","z":"float"}'
    >>> get_filter_condition_pgsql_string(python_types, 'z=7', '0')
    (' z = %s', [7.0])
    >>> get_filter_condition_pgsql_string(python_types, 'a=77', '1')
    (' a = %s', ['77'])
    """
    field, operator, obj_bind_val = get_filter_processed_3tuple(python_types, filter_urlencoded)
    #for now, bind target will just be sequential integer (likely started from 0)
    bind_target = str(start_bind)
    sql_equality_statement = '({} = %s)'
    sql_simple_access_predicate = " {} {} %s"
    sql_regexp_access_predicate = " {field} ~ %s"
    if operator == '~=':
        format_arguments = {'field' : field
                           }
        sql = sql_regexp_access_predicate.format( **format_arguments)
        return sql, [obj_bind_val]
    if operator == '|=':
        binds = []
        or_statements = [] # construct a set of ( () OR () ... ) equality expressions
        for bind_val in obj_bind_val:
            equality_statement = sql_equality_statement.format(field)
            or_statements.append( equality_statement)
            # add the values, into the binds list
            binds.append( bind_val)
            bind_target = str(start_bind + len(binds)) #increment label
        # now connect the set of expressions, with 'OR's
        or_clauses = " OR ".join(or_statements)
        # ... and append equality expression string-representation, to the current query
        access_clause = " ( {} )".format(or_clauses)
        return access_clause, binds
    #Else, just compose a simple access predicate
    access_clause = sql_simple_access_predicate.format(field
                                                       ,operator)
    return access_clause, [obj_bind_val]

def get_filter_condition_sqlalchemy_pgsql_string(python_types, filter_urlencoded, start_bind):
    """
    Convert HTTP filter to SQLAlchemy(pgsql) expression+bind value(s)

    SQLAlchemy requires text() parameter names in :format, even if the
    rest of the SQL expression contains PostgreSQL syntax/functions.

    Keyword Parameters:
    python_types  -- JSON encoded string representing a Dict that maps
      field names to Python type constructors
    filter_urlencoded  -- String, representing the HTTP filter
    start_bind  -- Integer representing the starting numeral to use
      for SQL bind variable identifier.

    Exceptions:
    FilterVariableError -- filters variable not found in header

    >>> from pprint import pprint
    >>> python_types = '{"a":"str","b":"int","z":"float"}'
    >>> get_filter_condition_sqlalchemy_pgsql_string(python_types, 'z=7', '0')
    (' z = :0', {'0': 7.0})
    >>> get_filter_condition_sqlalchemy_pgsql_string(python_types, 'a=77', '1')
    (' a = :1', {'1': '77'})
    >>> get_filter_condition_sqlalchemy_pgsql_string(python_types, 'z~=7', 0)
    (' z ~ :0', {'0': '7'})
    >>> out = get_filter_condition_sqlalchemy_pgsql_string(python_types, 'a|=["5", "77"]', 0)
    >>> pprint(out)
    (' ( (a = :0) OR (a = :1) )', {'0': '5', '1': '77'})
    """
    binds = {} #Dictionary, to return the numbered bind parameter Values
    field, operator, obj_bind_val = get_filter_processed_3tuple(python_types, filter_urlencoded)
    #for now, bind target will just be sequential integer (likely started from 0)
    bind_target = str(start_bind)
    sql_equality_statement = '({} = :{})'
    sql_simple_access_predicate = " {} {} :{}"
    sql_regexp_access_predicate = " {field} ~ :{bind}"
    if operator == '~=':
        format_arguments = {'field' : field
                           ,'bind'  : bind_target
                           }
        sql = sql_regexp_access_predicate.format( **format_arguments)
        binds[bind_target]=obj_bind_val
        return sql, binds
    if operator == '|=':
        or_statements = [] # construct a set of ( () OR () ... ) equality expressions
        for bind_val in obj_bind_val:
            equality_statement = sql_equality_statement.format(field, bind_target)
            or_statements.append( equality_statement)
            # add the values, into the binds Dict
            binds[bind_target]=bind_val
            bind_target = str(start_bind + len(binds)) #increment label
        # now connect the set of expressions, with 'OR's
        or_clauses = " OR ".join(or_statements)
        # ... and append equality expression string-representation, to the current query
        access_clause = " ( {} )".format(or_clauses)
        return access_clause, binds
    #Else, just compose a simple access predicate
    access_clause = sql_simple_access_predicate.format(field
                                                       ,operator
                                                       ,bind_target)
    binds[bind_target] = obj_bind_val
    return access_clause, binds


#TODO: these lambdas are dead code? refactor this map into a simple list.
dict_operator_map = collections.OrderedDict([
     ('>=', (lambda row_val, comp_val: row_val >= comp_val) )
    ,('<=', (lambda row_val, comp_val: row_val <= comp_val) )
    ,('!=', (lambda row_val, comp_val: row_val != comp_val) )
    ,('<' , (lambda row_val, comp_val: row_val < comp_val) )
    ,('>' , (lambda row_val, comp_val: row_val > comp_val) )
    ,('~=' , (lambda row_val, comp_val: re.compile( str(comp_val)).search( str(row_val)) is not None ) )
    ,('|=' , None )
    ,('=' , (lambda row_val, comp_val: row_val == comp_val) )
]); #These operators are specified in a specific order, so when checking '>=' is found before '='

def get_list_filter_partitioned( str_filter_urlencoded):
    """
    return list of right, operator, & left substrings, from URLdecoded filter

    >>> get_list_filter_partitioned( 'var=1')
    ['var', '=', '1']
    >>> get_list_filter_partitioned( 'var>=1')
    ['var', '>=', '1']
    >>> get_list_filter_partitioned( 'var<=1')
    ['var', '<=', '1']
    >>> get_list_filter_partitioned( 'var!=1')
    ['var', '!=', '1']
    >>> get_list_filter_partitioned( 'var<1')
    ['var', '<', '1']
    >>> get_list_filter_partitioned( 'var>1')
    ['var', '>', '1']
    >>> get_list_filter_partitioned( 'var~=1')
    ['var', '~=', '1']
    >>> get_list_filter_partitioned( 'var|=["1", "2"]')
    ['var', '|=', '["1", "2"]']
    """
    str_filter = urllib.parse.unquote(str_filter_urlencoded)
    #attempt to split into 3 strings
    list_of_operators = dict_operator_map.keys()
    for operator in list_of_operators:
        tuple_filter = str_filter.partition(operator)
        if tuple_filter[0] == str_filter:
            continue #No luck parsing,
        #Parsed! We matched an operator
        return list(tuple_filter)
    raise FilterParseError('Cannot parse: '+str_filter)

def get_filter_processed_3tuple( str_json_python_types, str_filter_urlencoded):
    """
    return tuple of field,operator string & Object bind value,from URLdecoded filter

    Keyword Parameters:
    str_json_python_types -- String representing a JSON Object, denominating
        data set fields & associated Python types.

    >>> test_func = get_filter_processed_3tuple
    >>> test_func( '{"var": "str", "baz": "float"}', 'var=1')
    ('var', '=', '1')
    >>> test_func( '{"var": "str", "baz": "float"}', 'var>=1')
    ('var', '>=', '1')
    >>> test_func( '{"var": "str", "baz": "float"}', 'var<=1')
    ('var', '<=', '1')
    >>> test_func( '{"var": "str", "baz": "float"}', 'var!=1')
    ('var', '!=', '1')
    >>> test_func( '{"var": "str", "baz": "float"}', 'var<1')
    ('var', '<', '1')
    >>> test_func( '{"var": "str", "baz": "float"}', 'var>1')
    ('var', '>', '1')
    >>> test_func( '{"var": "str", "baz": "float"}', 'var~=1')
    ('var', '~=', '1')
    >>> test_func( '{"name": "str", "score": "float"}', 'name=bob')
    ('name', '=', 'bob')
    >>> test_func( '{"name": "str", "score": "float"}', 'name=1.2')
    ('name', '=', '1.2')
    >>> test_func( '{"name": "str", "score": "float"}', 'score=1.2')
    ('score', '=', 1.2)
    >>> test_func( '{"name": "str", "score": "float"}', 'name|=["bob", "bif"]')
    ('name', '|=', ['bob', 'bif'])
    >>> test_func( '{"name": "str", "score": "float"}','score|=["1.2", "2.1"]')
    ('score', '|=', [1.2, 2.1])
    """
    #FIXME: above tests aren't very good
    try:
        list_parsed_elements = get_list_filter_partitioned( str_filter_urlencoded)
    except FilterParseError as e:
        raise e
    # now process the elements
    #FIXME: validate 'list_filter_elements' assumptions below
    str_left, str_operator, str_right = list_parsed_elements
    # Copy the left-element & operator, verbatim
    list_filter_parsed = []
    list_filter_parsed.append( str_left)
    list_filter_parsed.append( str_operator)
    # Identify Python type, for the left-hand element
    try:
        dict_types_by_field_name = json.loads( str_json_python_types)
        list_names_unknown_case = list(dict_types_by_field_name.keys())
        # Assume the left-hand element is the field name name
        int_index = get_index_caseinsensitive(str_left, list_names_unknown_case)
    except ValueError:
        # not found, abort!
        str_msg = 'Filters variable "{}" does not exist in data source'
        raise FilterVariableError( str_msg.format(str_left))
    
    # coerce the right-hand filter value,to type of left-hand Variable field
    try:
        str_field_name = list_names_unknown_case[int_index]
        str_field_type = dict_types_by_field_name[str_field_name]
        #locate constructor function
        type_constructor = pydoc.locate(str_field_type)
        if type_constructor is None:
            # Unknown type!
            raise SourceTypeError( str_field_type )
        if str_operator == '~=': #for RegExp, always attempt string comparison
            list_filter_parsed.append( str_right)
            return tuple(list_filter_parsed)
        if str_operator == '|=': #for OR equality, always attempt string comparison
            str_values = json.loads( str_right)
            values = [str_to_python_obj(x, type_constructor) for x in str_values]
            list_filter_parsed.append( values)
            return tuple(list_filter_parsed)
        #Else, attempt dynamic type coercion
        obj_right = str_to_python_obj( str_right, type_constructor)
        list_filter_parsed.append( obj_right)
        return tuple(list_filter_parsed)
    except TypeError as e:
        raise FilterValueError( str(e) )

def str_to_python_obj( str_value, type_constructor):
    """
    Utility function, for converting our parameter strings in Python objects.

    >>> str_to_python_obj( '1', str)
    '1'
    >>> str_to_python_obj( '2015-Jan-01', datetime.datetime)
    datetime.datetime(2015, 1, 1, 0, 0)
    >>> smart_default = str_to_python_obj( '2014', datetime.datetime)
    >>> smart_default
    datetime.datetime(2014, 1, 1, 0, 0)
    >>> str_to_python_obj( '1', float)
    1.0
    """
    if type_constructor == str: #no conversion needed
        return str_value
    if type_constructor == datetime.datetime: #attempt flexible date comparison
        parse_kwargs = { 'smart_defaults': True #treat 2014 as 1/1/2014
                       #FIXME: update requirements.txt; smart_defaults is an
                       # unreleased 'dateutil' feature, targeted for v2.4.3?
                       , 'fuzzy'         : True
                       }
        return dateutil.parser.parse( str_value, **parse_kwargs)
    #Else, attempt dynamic type coercion
    try:
        return type_constructor( str_value)
    except TypeError as e:
        raise FilterValueError( str(e) )

def is_filter_true( tuple_row, tuple_header, list_filter_elements):
    """
    test if a filter rule is true based on supplied headers, for referenced row

    Exceptions:
    FilterVariableError -- filters variable not found in header
    FilterValueError -- filters value could not be parsed

    >>> is_filter_true( (7,), ('v1',), ['v1','=',7])
    True
    >>> is_filter_true( ('str',), ('v1',), ['v1','=','str'])
    True
    >>> dt = datetime.datetime(1970,1,13)
    >>> is_filter_true( (dt,), ('v1',), ['v1','=',datetime.datetime(1970,1,13)])
    True
    >>> is_filter_true( (dt,), ('v1',), ['v1','=',datetime.datetime(4970,1,14)])
    False
    >>> is_filter_true( (dt,), ('v1',), ['v1','~=','1971'])
    False
    >>> is_filter_true( (dt,), ('v1',), ['v1','~=','^(1970-01-13 00:00:00)$'])
    True
    """
    str_left = list_filter_elements[0]
    str_operator = list_filter_elements[1]
    obj_right = list_filter_elements[2]
    #FIXME: validate assumptions below
    # assume the left side is the Variable name
    try:
        # determine the tuple index of this variable
        int_index = get_index_caseinsensitive(str_left, tuple_header)
    except ValueError:
        # not found, abort!
        str_msg = 'filters variable {} does not exist in data source'
        raise FilterVariableError( str_msg.format(str_left))
    
    # check if value matches, via our map of comparitor functions.
    try:
        operator_function = dict_operator_map[str_operator]
        obj_variable = tuple_row[int_index]
        return operator_function(obj_variable, obj_right)
    except KeyError:
        # Operator not found in our map; perform no filtering.
        return True
