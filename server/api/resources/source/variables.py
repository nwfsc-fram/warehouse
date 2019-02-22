"""
Module providing a RESTful endpoint,representing a source's available variables

Copyright (C) 2015, 2016 ERT Inc.
"""
import falcon
import api.json as json
import api.resources.source.warehouse.warehouse as warehouse
from api.resources.source import (
    source
    ,parameters as source_parameters
)
from api.auth import auth
from api.resource_util import ResourceUtil
import api.config_loader as loader
import logging

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

str_route = 'variables'
"""
String representing the URI path for this endpoint

E.g., "/{id}/variables"
"""

class RoleTitleTableUnknown(ValueError):
    """
    raised when 'variable' table is not found in provided table list
    """
    pass

class RoleTitleRoleUnknown(ValueError):
    """
    'variable' parent Role is not found in provided associations list
    """
    pass

class RoleTitleDimensionUnknown(ValueError):
    """
    'variable' parent Role's base Dimension is not found in tables list
    """
    pass

class Variables:
    """
    A Falcon resource object, representing a dataset's variables
    """

    def on_get(self, request, resp, **kwargs):
        """
        Falcon resource method, for handling HTTP request GET method

        Falcon request provides: parameters embedded in URL via a keyword args
        dict, as well as convenience class variables falcon.HTTP_*
        """
        api_config = loader.get_api_config()
        request_url = ResourceUtil.get_request_url(request, api_config)

        with warehouse.get_source_model_session() as model:
            sources = source.SourceUtil.get_list_of_data_sources(request_url
                                                                 ,auth.get_user_id(request)
                                                                 ,model)
            str_dataset_id = source_parameters.get_requested_dataset_id(sources
                                                                        ,request
                                                                        ,resp
                                                                        ,kwargs)
            dict_variables = ResourceUtil.get_self_dict(request_url)
            try:
                dwsupport_variables = get_list_of_variables( str_dataset_id)
            except NotImplementedError as e:
                #error; not a warehouse request & Dataset does not match requested ID
                logging.exception(e)
                raise falcon.HTTPError(falcon.HTTP_NOT_IMPLEMENTED, 'Not Implemented', str(e))
            # format the DWSupport info, for publishing
            tables, associations = model['tables'], model['associations']
            list_variables = [to_web_variable(v, tables, associations)
                              for v in dwsupport_variables]
            # alphabatize the fields
            list_variables.sort(key=lambda v:v['id'])
            dict_variables[str_route] = list_variables
            str_nesting_indent_char = '\t'
            resp.body = json.dumps( dict_variables, indent=str_nesting_indent_char)

def get_list_of_variables( str_dataset_id):
    """
    Returns a list of dicts,representing all of source's available variables

    Keyword Parameters:
    str_dataset_id  -- String, representing API id for the dataset
    """
    if warehouse.is_warehouse( str_dataset_id):
        return warehouse.get_list_of_warehouse_variables()
    list_variables = []
    for dict_source in loader.get_list_of_etl_dicts():
        if dict_source['id'] == str_dataset_id:
            # retrieve & decode the configured list of fields+types
            str_field_types_json = dict_source['python_types']
            dict_field_types = json.loads( str_field_types_json)
            # add the field names, to our list
            list_variables.extend( dict_field_types.keys())
            return list_variables
    # if loop did not return,continue search through db-configured sources
    # break dataset identifier down into project/source substrings
    with warehouse.get_source_model_session() as current_model:
        project_name, source_name = str_dataset_id.split('.')
        source_tables = warehouse.get_source_tables()
        for source_table in source_tables:
            if source_table['name'] == source_name:
                variables_by_field = {}
                source_type = source_table['type']
                if not source_type in ['fact','dimension','dimension role']:
                    #TODO: Make exception into a locally defined class
                    raise NotImplementedError('no method to list variables for {} tables: {}'.format(source_type,source_name))
                if source_type == 'fact':
                     two_dicts = warehouse.get_fact_variables(source_table, current_model)
                     variables_by_field, unused = two_dicts
                if source_type == 'dimension':
                    # retrieve the fields -to-types mapping
                    variables_by_field = warehouse.get_variables(source_table)
                if source_type == 'dimension role':
                    # retrieve aliased versions, of underlying dimension's mapping
                    variables_by_field = warehouse.get_role_variables(source_table)
                # add the variable dicts, to our list
                list_variables.extend(variables_by_field.values())
                return list_variables
        else:
            str_msg = 'Unable to list variables, source id {} not found.'
            raise falcon.HTTPNotFound( description=str_msg.format(str_dataset_id))

def _get_role_title(variable, tables, associations):
    """
    returns String representing variable Title with relevant Role info

    Keyword Parameters:
    variable  -- Warehouse 'variable' data transfer object
    tables  -- List, of all Warehouse 'table' data transfer objects
    associations -- List, of all Warehouse 'association' DTOs

    Exceptions:
    RoleTitleTableUnknown  -- raised when 'variable' table not found
      in referenced list of 'tables'
    RoleTitleRoleUnknown  -- raised when 'variable' table is a Role but
      is not found in referenced list of 'associations'
    RoleTitleDimensionUnknown  -- raised when 'variable' table Role's
       base Dimension 'association' cannot be found in the list of
      'tables'

    >>> all_tables = [ { 'name': 'depth_dim', 'type': 'dimension'
    ...                 ,'description': 'Depth which has been described in a'
    ...                              ' very verbose way', 'title': 'Depth Dim'}
    ...               ,{ 'name': 'best_depth_dim'
    ...                 ,'type': 'dimension role', 'title': 'Best Depth Dim'
    ...                 ,'description': 'Best Depth also described verbosely'}]
    >>> all_association = [{ 'table': 'best_depth_dim'
    ...                     ,'parent': 'depth_dim'}]
    >>> var_role = {'title': 'Depth (m)', 'table': 'best_depth_dim'}
    >>> _get_role_title(var_role, all_tables
    ...                 ,all_association) #expecting role prefix
    'Best Depth (m)'
    >>> _get_role_title(var_role, all_tables
    ...                 ,[]) #expecting Role exception
    Traceback (most recent call last):
       ...
    api.resources.source.variables.RoleTitleRoleUnknown: (best_depth_dim) not found in provided associations
    >>> _get_role_title(var_role, all_tables[-1:]
    ...                 ,all_association) #expecting Dimension exception
    Traceback (most recent call last):
       ...
    api.resources.source.variables.RoleTitleDimensionUnknown: (depth_dim) not found in provided tables
    >>> var_dim_lookup = {'title': 'Depth (m)', 'table': 'depth_dim'}
    >>> _get_role_title(var_dim_lookup, all_tables
    ...                 ,all_association) #no change expected
    'Depth (m)'
    >>> var_fact_attribute = {'title': 'Frob (Hz)', 'table': 'frob_fact'}
    >>> _get_role_title(var_fact_attribute, all_tables
    ...                 ,all_association) #exception expected
    Traceback (most recent call last):
       ...
    api.resources.source.variables.RoleTitleTableUnknown: (frob_fact) not found in provided tables
    >>> fact = { 'name': 'frob_fact', 'type': 'fact','description': 'Frobing'}
    >>> _get_role_title(var_fact_attribute, all_tables+[fact]
    ...                 , all_association) #no change expected
    'Frob (Hz)'
    >>> tables_missing_title = [ { 'name': 'depth_dim'
    ...                              ,'type': 'dimension', 'title': None
    ...                              ,'description': 'A greath Depth Dim description'}
    ...                             ,{ 'name': 'best_depth_dim'
    ...                               ,'type': 'dimension role', 'title': 'Best Depth Dim'
    ...                               ,'description': 'Best Depth'}]
    >>> _get_role_title(var_role, tables_missing_title
    ...                 ,all_association) #expecting No role prefix!
    'Depth (m)'
    """
    # find the 'table' this variable comes from
    variable_table_name = variable['table']
    for table in tables:
        if table['name'] == variable_table_name:
            variable_table = table
            break
    else:
        msg = "({}) not found in provided tables"
        raise RoleTitleTableUnknown(msg.format(variable_table_name))

    # check if Title must be modified (because table is an OLAP Role)
    if variable_table['type'] == 'dimension role':
        role = variable_table #variable belongs to an OLAP Role
        #identify parent dimension, of this Role
        for association in associations:
            if association['table'] == role['name']:
                role_parent_name = association['parent']
                break
        else:
            msg = "({}) not found in provided associations"
            raise RoleTitleRoleUnknown(msg.format(role['name']))
        # find 'table' for this Role's base dimension
        for table in tables:
            if table['name'] == role_parent_name:
                base_dimension = table
                break
        else:
            msg = "({}) not found in provided tables"
            raise RoleTitleDimensionUnknown(msg.format(role_parent_name))
        #munge title, using the OLAP Role's description
        role_description, dim_description = ( role['title']
                                             ,base_dimension['title'])
        if all([role_description, dim_description]):
            role_prefix = role_description.replace(dim_description, '')
            return role_prefix + variable['title']
        # Description was null! cannot munge
    #otherwise, return title unmodified
    return variable['title']

def to_web_variable(dwsupport_variable, tables, associations):
    """
    returns Dict representing a stripped & modified DWSupport variable

    Keyword Parameters:
    dwsupport_variable  -- Warehouse data transfer object, representing
      a warehouse data field.

    >>> from pprint import pprint
    >>> var1 = { 'column':'frob_hz', 'title':'Frobniz Resonance (Hz)'
    ...         ,'python_type': 'float', 'physical_type': 'numeric'
    ...         ,'table': 'foo_fact', 'max_length': 147456
    ...         ,'units': 'hertz', 'precision': 16383
    ...         ,'description': 'A useful value!'
    ...         ,'allowed_values': '1+e-16383 - 9e147456'}
    >>> tables = [ { 'name': 'foo_fact', 'type': 'fact'
    ...             ,'description': 'Foo Study'}]
    >>> associations = []
    >>> pprint(to_web_variable(var1, tables, associations))
    {'allowed_values': '1+e-16383 - 9e147456',
     'description': 'A useful value!',
     'id': 'frob_hz',
     'max_length': 147456,
     'precision': 16383,
     'title': 'Frobniz Resonance (Hz)',
     'type': 'float',
     'units': 'hertz'}
    >>> var1['python_type'] = 'datetime.datetime'
    >>> out = to_web_variable(var1, tables, associations)
    >>> out['type']
    'ISO 8601 datetime'
    """
    web_variable = {}
    published_fields = [
        'column'
        ,'title'
        ,'description'
        ,'units'
        ,'max_length'
        ,'precision'
        ,'python_type'
        ,'allowed_values']
    for key in published_fields:
        web_key = key
        web_value = dwsupport_variable[key]
        #potentially, make some changes to either key, value or both
        if key == 'column': #rename to ID,since some have been prefixed w/ dim
            web_key = 'id' #saying api ID is more accurate, than 'column'
        if key == 'python_type': #Rename key to 'type'
            web_key = 'type'
            #describe what it is, instead of using full Python module date name
            if dwsupport_variable[key] == 'datetime.datetime':
                web_value = 'ISO 8601 datetime'
        if key == 'title': #munge title value if var is from a Role lookup
            web_value = _get_role_title(dwsupport_variable, tables, associations)
        #save value as key
        web_variable[web_key] = web_value
    return web_variable
