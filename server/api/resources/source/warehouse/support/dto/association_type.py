"""
Module,providing a metadata DAO api for types of associations between DW tables

Data warehouse tables typically associate as dimensional lookup tables, for one
or more fact summary tables.

Copyright (C) 2016 ERT Inc.
"""
from api.resources.source.warehouse.support import dto_util
import sqlalchemy

TABLE = "table_relation_type"
# support table, containing the list of all possible association types

class ValidateTypeError(TypeError):
    """
    Exception raised when the type of a Warehouse association_type is not a
     dictionary.
    """
    pass
class ValidateMissingValue(ValueError):
    """
    Raised when a required, warehouse association_type attribute is absent.
    """
    pass
class ValidateUnexpectedValue(ValueError):
    """
    Raised when an unrecognized, warehouse Association_type attribute is
    encountered.
    """
    pass

def get_all():
    """
    returns list of all accepted association types.

    >>> from pprint import pprint
    >>> types = get_all()
    >>> pprint(types, width=78)
    [{'description': 'Relation (child) table represents a set of measured facts '
                     'with a dimension key which can be looked up in a parent '
                     '(Dimension) table to obtain supplemental, descriptive '
                     'information about each fact.',
      'name': 'fact dimension'},
     {'description': 'Relation (child) table represents a set of measured facts '
                     'which can be looked up in a parent (fact aggregate) table '
                     'by way conformed dimensions, to obtain summarized '
                     'information about each category of fact.',
      'name': 'fact summary'},
     {'description': 'Relation (child) table represents a set of measured facts '
                     'with a dimension key that can be looked up in a parent '
                     '(Dimensional Role) table to obtain supplemental, '
                     'descriptive info about each fact. Roles are Dimension '
                     'aliases, when Dims are used for specific purposes.',
      'name': 'fact dimension role'},
     {'description': 'Relation (child) table represents a Dimensional Role, an '
                     'alias for a parent (Dimension) table.',
      'name': 'dimension role base'}]
    """
    # define default values
    fact_dim = {'name': 'fact dimension'
               ,'description':
                   'Relation (child) table represents a set of measured facts '
                   'with a dimension key which can be looked up in a parent '
                   '(Dimension) table to obtain supplemental, descriptive '
                   'information about each fact.'}
    fact_sum = {'name': 'fact summary'
               ,'description':
                   'Relation (child) table represents a set of measured facts '
                   'which can be looked up in a parent (fact aggregate) table '
                   'by way conformed dimensions, to obtain summarized '
                   'information about each category of fact.'}
    fact_role = {'name': 'fact dimension role'
               ,'description':
                   'Relation (child) table represents a set of measured facts '
                   'with a dimension key that can be looked up in a parent '
                   '(Dimensional Role) table to obtain supplemental, '
                   'descriptive info about each fact. Roles are Dimension '
                   'aliases, when Dims are used for specific purposes.'}
    role_dim = {'name': 'dimension role base'
               ,'description':
                   'Relation (child) table represents a Dimensional Role, an '
                   'alias for a parent (Dimension) table.'}
    return [fact_dim, fact_sum, fact_role, role_dim]

def validate( association_type):
    """
    validates if referenced object conforms to this module's api for
    association types.

    Keyword Parameters:
    assocation_type  --  dictionary, representing a type of table association.

    Exceptions:
    ValidateTypeError -- raised when association_type parameter is not a dictionary
    ValidateMissingValue -- raised when association_type parameter is incomplete
    ValidateUnexpectedValue -- raised when association_type parameter is malformed

    >>> from copy import deepcopy
    >>> assoc1 = {'name': 'fact dimension', 'description': 'Relation (child) table represents a set of measured facts with a dimension key which can be looked up in a parent (Dimension) table to obtain supplemental, descriptive information about each fact.'}
    >>> validate( assoc1)
    True
    >>> validate( 'NotADict')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.association_type.ValidateTypeError: <class 'str'>
    >>> validate( {'name': 'fact dimension', 'description': 'SomeUnrecognizedText!'})
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.association_type.ValidateUnexpectedValue: description="SomeUnrecognizedText!" not defined in get_all()
    >>> missing = deepcopy( assoc1); removed = missing.pop('name')
    >>> validate( missing)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.association_type.ValidateMissingValue: name
    >>> extra = deepcopy( assoc1); extra['Foo'] = 'anything'
    >>> validate( extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.association_type.ValidateUnexpectedValue: Foo
    """
    if not isinstance( association_type, dict):
        raise ValidateTypeError( type(association_type) )
    # verify object structure
    expected_keys = ['name','description']
    for key in expected_keys: #check that *all* attributes are present
        if key not in association_type.keys():
            raise ValidateMissingValue( key)
    for key in association_type.keys(): #check for any non-standard attributes
        if key not in expected_keys:
            raise ValidateUnexpectedValue( key)
    # verify object contents
    for key in expected_keys:
        if association_type[key] not in [a[key] for a in get_all()]:
            name = association_type[key]
            msg = '{}="{}" not defined in get_all()'.format(key, name)
            raise ValidateUnexpectedValue( msg)
    # otherwise, must be Ok!
    return True

def save(association_types, db_url=None, connection_func=None):
    """
    persists a list of one (or more) association_type, to the warehouse database

    Keyword Parameters:
    association_types  --  list of types for association
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> import datetime
    >>> empty_list = []
    >>> save( [])
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    insert_statement = ('INSERT INTO {schema}.{table} ('
                        '   type_name'
                        '  ,description'
                        ') VALUES ('
                        '   %(name)s'
                        '  ,%(description)s'
                        ')'
                       ).format(schema=dto_util.SCHEMA,table=TABLE)
    dto_util.exec_base( association_types, validate, insert_statement
                       ,db_url=db_url, connection_func=connection_func)
