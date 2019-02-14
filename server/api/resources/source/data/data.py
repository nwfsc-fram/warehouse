"""
Utility module, encapsulating how Data is retrieved from the backing sources

Copyright (C) 2015, 2016 ERT Inc.
"""
import traceback

import waitress

from . import util
from api.resources.source.warehouse import warehouse
from api.resources.source.warehouse.support.dto import table, table_type, variable
from api.resources.source.selection import parameters, pivot, auth
from api import (
    json
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "
__all__ = ['NoSourceException'
    ,'get_data'
    ,'get_result_from_db']

class NoSourceException(Exception):
    # raised when no matching dataset ID can be found
    pass

class NotAuthorizedException(Exception):
    # raised when requesting User is not permitted access to dataset
    pass

def get_data(str_source_id, variables=[], filters=[], columns=[]
             ,empty_cell_dimensions=[],user_id=None):
    """
    returns list db result rows from referenced source, w/ 1x 'header' row prepended

    Exceptions:
    NoSourceException -- raised when no dataset matches str_source_id
    FilterVariableError -- filters variable not found in header
    NotAuthorizedException  -- user_id not authorized to select data
      from the specified source.
    
    >>> test_source_id = 'NoBackendAvailableForUnitTests'
    >>> data_list = get_data(test_source_id)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.model.prefetch_cache.NoDataError
    """
    if warehouse.is_warehouse(str_source_id):
        #TODO: implement sensitive data tables
        return warehouse.get_result(user_id, variables=variables, filters=filters) #TODO: implement EMPTY cell support
    #Else, return data from the source directly
    return get_result_from_db(str_source_id, variables, filters, columns
                              ,empty_cell_dimensions,user_id)

def get_result_from_db(str_source_id, variables=[], filters=[], columns=[]
                       ,empty_cell_dimensions=[], user_id=None):
    """
    returns list of db result rows, w/ 1x 'header' row prepended

    Keyword Parameters:
    str_source_id -- String, representing requested dataset's API id
    variables  -- list of requested variable names
    filters  -- list of specified filter expression strings
    columns  -- list of names for requested dimension variables to
      be pivoted as additional columns,for all requested value variables
    empty_cell_dimensions  -- list of Strings representing Dimension
       tables (or OLAP-Roles) which are to be OUTER JOINED to produce
       empty Fact value cells for all Dimensional values not found in
       the fact.
    user_id  -- String, representing an authenticated User principal

    Exceptions:
    FilterVariableError -- filters variable not found in header
    NoSourceException -- raised when no dataset matches str_source_id
    NotAuthorizedException  -- user_id not authorized to select data
      from the specified source.

    """
    #generate query
    tables = warehouse.get_source_tables()
    # break dataset identifier down into project/source substrings
    project_name, source_name = str_source_id.split('.')
    for warehouse_table in tables:
        if warehouse_table['name'] == source_name:
            # get connection
            connection = util._get_source_connection( warehouse.dict_source)
            with warehouse.get_source_model_session() as cached_model:
                if warehouse_table['confidential']:
                    # Attempt to obtain a sensitive connection IF user is authorized
                    if not auth.is_select_permitted(user_id, warehouse_table
                                                    ,cached_model):
                        raise NotAuthorizedException()
                    connection.close()
                    connection = util._get_source_connection({'id':'Fake .ini source','db_file':'db_dwsensitive.ini'})
                # retrieve filter info
                if warehouse_table['type'] == 'fact':
                    two_dicts = warehouse.get_fact_variables(warehouse_table, cached_model)
                    variable_by_field, unused = two_dicts
                if warehouse_table['type'] == 'dimension':
                    variable_by_field = warehouse.get_variables(warehouse_table)
                if warehouse_table['type'] == 'dimension role':
                    variable_by_field = warehouse.get_role_variables(warehouse_table)
                python_types = {}
                for field in variable_by_field:
                    var = variable_by_field[field]
                    python_types[field] = var['python_type']
                json_python_types = json.dumps(python_types)
                # get sql & binds
                try:
                    table_type.validate( warehouse_table['type'])
                except table_type.ValidateUnexpectedValue as e:
                    raise NotImplementedError('No SQL Generation method, for type: {}'.format(warehouse_table)) from e #TODO: make this into a local class
                sql_with_filters, binds = warehouse.get_sql_filtered(
                    warehouse_table
                    ,json_python_types
                    ,filters
                    ,empty_cell_dimensions)
                db_config_file_name = warehouse.dict_source['db_file']
                break # source found, exit!
    else:
        raise NoSourceException(e)
    if len(binds) > 0:
        result = connection.execution_options(stream_results=True).execute(sql_with_filters, binds)
    else:
        result = connection.execution_options(stream_results=True).execute(sql_with_filters)
    # compose results list
    result_generator = database_row_generator(result, connection)

    subset_generator = parameters.get_result_subset(result_generator, variables)
    if columns:
        # pivot, i.e.: replace 'columns' fields & all measured value
        # fields with new measured-value breakdowns for the 'columns'
        # field values.
        all_variables = warehouse.get_source_variables()
        fact_variables = [v for v in all_variables if v['table']==source_name]
        return pivot.get_result(subset_generator, columns, fact_variables)
    #else, no pivot needed - just return
    return subset_generator

def database_row_generator(result, connection):
    """
    efficiently stream unfiltered results from database
    """
    yield tuple(result.keys()) # return an initial 'header' tuple
    while True:
        next_rows = result.fetchmany(50)
        if next_rows == []:
            break #No more data rows (exit the loop)
        for row in next_rows:
            yield row # return 'data' tuples
    connection.close() # all data retrieved, release cursor/connection
    raise StopIteration
