"""
Python module, to dump and load DWSupport content from persistence

Copyright (C) 2016-2017 ERT Inc.
"""
from pprint import pformat
import difflib

from ..dto import (
    project
    ,contact
    ,table
    ,table_type
    ,association
    ,association_type
    ,query
    ,variable
    ,variable_custom_identifier
    ,variable_python_type
    ,table_authorization
    ,management_authorization
)

class ValidateTypeError(TypeError):
    """
    Exception raised when DWSupport model type is not Dict
    """
    pass
class ValidateMissingValue(ValueError):
    """
    Raised when a required, DWSupport model attribute is absent
    """
    pass
class ValidateUnexpectedValue(ValueError):
    """
    Unrecognized DWSupport model attribute encountered
    """
    pass
class ValidateValueTypeError(TypeError):
    """
    Exception raised when a DWSupport model attribute is not a List
    """
    pass

def validate( model):
    """
    validate if referenced object conforms to api for a DWSupport model

    Keyword Parameters:
    model -- dictionary representing a DWSupport warehouse configuration
      model.

    Exceptions:
    ValidateTypeError -- raised when model is not a Dict
    ValidateMissingValue -- raised when model is incomplete
    ValidateUnexpectedValue -- raised when model is malformed
    ValidateValueTypeError -- raised when a model attribute is malformed

    >>> from copy import deepcopy
    >>> empty_model = {'projects': []
    ...                ,'contacts': []
    ...                ,'table_types': []
    ...                ,'association_types': []
    ...                ,'queries': []
    ...                ,'variable_custom_identifiers': []
    ...                ,'variable_python_types': []
    ...                ,'tables': []
    ...                ,'associations': []
    ...                ,'variables': []
    ...                ,'table_authorizations': []
    ...                ,'management_authorizations': []}
    >>> validate(empty_model)
    True
    >>> json_model = '{"projects": [{"name":"invalid","title": "Json String"}]}'
    >>> validate(json_model)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.model.model.ValidateTypeError: <class 'str'>
    >>> validate( {'extra': 'Thing'})
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.model.model.ValidateUnexpectedValue: extra
    >>> validate( {})
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.model.model.ValidateMissingValue: projects
    """
    # verify object type
    if not isinstance(model, dict):
        raise ValidateTypeError(type(model))
    # verify model contents
    expected_property_names = ['projects','table_types','association_types'
                               ,'queries'
                               ,'variable_custom_identifiers'
                               ,'variable_python_types','tables','associations'
                               ,'variables','contacts','table_authorizations'
                               ,'management_authorizations']
    for model_property in model:
        if model_property not in expected_property_names:
            raise ValidateUnexpectedValue(model_property)
        # confirm attribute value is a list
        property_value = model[model_property]
        if not isinstance(property_value, list):
            #alert which property failed + what the type was
            msg = '{}({})'.format(model_property,type(model))
            raise ValidateValueTypeError(msg)
    # check for missing contents
    for expected_property in expected_property_names:
        if expected_property not in model:
            raise ValidateMissingValue(expected_property)
    # must be good!
    return True

def pretty_diff( model_a, model_b):
    """
    Return a string, representing a Unified diff of two models

    >>> from copy import deepcopy
    >>> from pprint import pprint
    >>> empty_model = {'projects': []
    ...                ,'contacts': []
    ...                ,'table_types': []
    ...                ,'association_types': []
    ...                ,'variable_custom_identifiers': []
    ...                ,'variable_python_types': []
    ...                ,'tables': []
    ...                ,'associations': []
    ...                ,'variables': []}
    >>> another_empty_model = {'projects': []
    ...                ,'contacts': []
    ...                ,'table_types': []
    ...                ,'association_types': []
    ...                ,'variable_custom_identifiers': []
    ...                ,'variable_python_types': []
    ...                ,'tables': []
    ...                ,'associations': []
    ...                ,'variables': []}
    >>> pretty_diff( empty_model, another_empty_model)
    ''
    >>> partial_model = deepcopy(empty_model)
    >>> partial_model['table_types'] = ['fact']
    >>> pprint( pretty_diff( empty_model, partial_model))
    ('--- \\n'
     '\\n'
     '+++ \\n'
     '\\n'
     '@@ -2,7 +2,7 @@\\n'
     '\\n'
     "  'associations': [],\\n"
     "  'contacts': [],\\n"
     "  'projects': [],\\n"
     "- 'table_types': [],\\n"
     "+ 'table_types': ['fact'],\\n"
     "  'tables': [],\\n"
     "  'variable_custom_identifiers': [],\\n"
     "  'variable_python_types': [],")
    """
    get_string_rep = lambda m: pformat(m).split('\n')
    model_string_a = get_string_rep(model_a)
    model_string_b = get_string_rep(model_b)
    diff_generator = difflib.unified_diff(model_string_a, model_string_b)
    return '\n'.join([string for string in diff_generator])

def dump(db_url=None, connection_func=None):
    """
    extracts & returns the persisted DWSupport configuration as a Dict

    Keyword Parameters:
    db_url  --  String, representing a SQLAlchemy connection (Required,
      if parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArguments  -- raised if neither connection or
      db_url parameter is specified.

    >>> dump()
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    get_args = [db_url, connection_func]
    model = {"projects": project.get_all(*get_args)
            ,"table_types": table_type.get_all()
            ,"association_types": association_type.get_all()
            ,"variable_custom_identifiers": variable_custom_identifier.get_all(*get_args)
            ,"variable_python_types": variable_python_type.get_all()
            ,"tables": table.get(*get_args)
            ,"contacts": contact.get_all(*get_args)
            ,"associations": association.get_all(*get_args)
            # variables.get() has 1x more parameter,than the others
            ,"variables": variable.get(db_url=db_url, connection_func=connection_func)
            ,"table_authorizations": table_authorization.get_all(*get_args)
            ,"management_authorizations": management_authorization.get_all(*get_args)
            ,"queries": query.get_all(*get_args)
    }
    # sort lists, to support comparing models from different physical sources
    for attribute_key in model:
        attribute_list = model[attribute_key]
        attribute_list.sort(key=pformat) #sort in-place
    for warehouse_query in model['queries']:
        for query_table in warehouse_query['variables'].values():
            query_table.sort(key=pformat) #sort
    validate( model)
    return model

def load(model, db_url=None, connection_func=None):
    """
    replaces the persisted DWSupport configuration with referenced model

    Keyword Parameters:
    model  -- Dict, representing a complete DWSupport configuration
    db_url  --  String, representing a SQLAlchemy connection (Required,
      if parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArguments  -- raised if neither connection or
      db_url parameter is specified.
    ValidateTypeError -- raised when model is not a Dict
    ValidateMissingValue -- raised when model is incomplete
    ValidateUnexpectedValue -- raised when model is malformed
    ValidateValueTypeError -- raised when a model attribute is malformed

    >>> load( {'anything': 1})
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.model.model.ValidateUnexpectedValue: anything
    """
    validate(model)
    db_args = {'db_url': db_url, 'connection_func': connection_func}
    # clear existing model
    #TODO: implement clearing/updating existing content!
    # save new model
    project.save(model['projects'], **db_args)
    contact.save(model['contacts'], **db_args)
    table_type.save(model['table_types'], **db_args)
    association_type.save(model['association_types'], **db_args)
    #TODO: implement variable_custom_identifiers save.
    variable_python_type.save(model['variable_python_types'], **db_args)
    table.save( model['tables'], **db_args)
    association.save( model['associations'], **db_args)
    variable.save( model['variables'], **db_args)
    authorization.save( model['table_authorizations'], **db_args)
    #TODO: implement queries save
