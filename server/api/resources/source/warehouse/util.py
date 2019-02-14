"""
Module containing shared source.warehouse helper functions

Copyright (C) 2016 ERT Inc.
"""
from api.resources.source.data import util

str_source_variable_separator = '$'
#String value,to make unique field names from Source dataset ID & Source field

def get_dwsupport_connection():
    """
    returns pooled connection to DB instance with DWSupport tables

    >>> get_dwsupport_connection() #Unittest expects NO working db connection
    Traceback (most recent call last):
       ...
    api.resources.source.data.util.ConfigDbConnectError: db_dwsupport.ini
    """
    dict_source_support = {'id':'Fake .ini source','db_file':'db_dwsupport.ini'}
    #Dict, conformed to server/etl_config.ini format &specifying DWSupport db config

    return util._get_source_connection(dict_source_support)

def prefix_field_name( str_field, str_source_id):
    """
    Utility function,creating unique field name for referenced field+Dataset id

    >>> prefix_field_name( 'outcome', 'ollie.pats_face')
    'ollie.pats_face$outcome'
    """
    return ''.join([str_source_id, str_source_variable_separator, str_field])
    
def get_field_name(variable_id):
    """
    Returns the referenced variable_id with the Dataset prefix removed
    
    >>> get_field_name('newhart_family$bob')
    'bob'
    >>> get_field_name('my_dimension_field')
    'my_dimension_field'
    """
    return variable_id.split(str_source_variable_separator).pop()

def get_custom_variable_name(variable, model):
    """
    Returns model's Custom ID for referenced variable, or None

    variable  -- dictionary, represnting an DWSupport 'Variable' Data
      Transfer Object (DTO).
    model  -- dictionary of lists, representing warehouse configuration
      model.

    >>> from pprint import pprint
    >>> variable = {'table': 'good_fact', 'column': 'great_field_name'}
    >>> model = {'variable_custom_identifiers': []}
    >>> out = get_custom_variable_name(variable, model)
    >>> pprint(variable)
    {'column': 'great_field_name', 'table': 'good_fact'}
    >>> out
    >>> model = {'variable_custom_identifiers': [{ 'table': 'good_fact'
    ...                                           ,'column': 'great_field_name'
    ...                                           ,'id': 'Test!'}]}
    >>> get_custom_variable_name(variable, model)
    'Test!'
    >>> pprint(variable)
    {'column': 'great_field_name', 'table': 'good_fact'}
    >>> dim_variable = {'table': 'good_dim', 'column': 'okay_field_name'}
    >>> dim_model = {'variable_custom_identifiers': [{ 'table': 'good_dim'
    ...                                               ,'column': 'okay_field_name'
    ...                                               ,'id': 'okay'}]}
    >>> get_custom_variable_name(dim_variable, dim_model)
    'okay'
    >>> pprint(dim_variable)
    {'column': 'okay_field_name', 'table': 'good_dim'}
    """
    variable_custom_identifiers = model['variable_custom_identifiers']
    web_name = None
    initial_variable_id = variable['column']
    dwsupport_column_name = get_field_name(initial_variable_id)
    for variable_custom_id in variable_custom_identifiers:
        if (variable_custom_id['table'] == variable['table']
                and variable_custom_id['column'] == dwsupport_column_name):
            web_name = variable_custom_id['id']
            break
    return web_name
