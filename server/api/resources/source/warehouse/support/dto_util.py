"""
Module,providing common functionality used by all support Data Transfer Objects

Copyright (C) 2016 ERT Inc.
"""
from copy import deepcopy
import logging
import itertools
import ast

import sqlalchemy

SCHEMA = 'dwsupport'
# Name of the schema containing the Warehouse metadata tables

class ConnectionMissingArgument(ValueError):
    """
    Raised when save() is called with insufficient arguments.
    """
    pass
class ExecMissingArgument(ValueError):
    """
    Raised when exec_base() is called with insufficient arguments.
    """
    pass
class ValidateException(Exception):
    """
    Exception raised when a metadata Data Transfer Object fails validation.
    """
    pass
class DimensionRoleError(ValueError):
    """
    Raised when get_roles() can't derive a role name from FK constraint
    """
    pass

def decode_years_to_min_max(summarized_year_string):
    """
    decode a summarized string of years into minimum & max. year values

    >>> decode_years_to_min_max('2000-2002, 2004')
    (2000, 2004)
    >>> decode_years_to_min_max('1992, 1994-1995')
    (1992, 1995)
    >>> decode_years_to_min_max('1750, 1752')
    (1750, 1752)
    >>> decode_years_to_min_max('1750-1751')
    (1750, 1751)
    >>> decode_years_to_min_max('1901')
    (1901, 1901)
    """
    tokens = []
    # split summary into groups of sequential digits or sequental non-digits
    for match, group_iterator in itertools.groupby(summarized_year_string
                                                   ,key=str.isdigit):
        group_string = ''.join(group_iterator)
        tokens.append(group_string)
    # pick off the first & last groups
    min_string = tokens[0]
    max_string = tokens[-1]
    return int(min_string), int(max_string)

def format_years( year_numbers):
    """
    format a collection of numerical years into a summarized string

    >>> format_years( {1901})
    '1901'
    >>> format_years( {1750, 1751})
    '1750-1751'
    >>> format_years( {1750, 1752})
    '1750, 1752'
    >>> format_years( {1992, 1994, 1995})
    '1992, 1994-1995'
    >>> format_years( {2000, 2001, 2002, 2004})
    '2000-2002, 2004'
    """
    years_list = list(year_numbers)
    years_list.sort()

    output = ''

    # scan the list of years & identify ranges or single items
    possible_range_end = None
    for list_index,year in enumerate(years_list):
        # start the output
        if list_index == 0:
            output += str(year)
            continue #skip to next year

        # check for a contiguous range of years
        previous_year = years_list[list_index-1]
        if year == previous_year+1:
            possible_range_end = year
            continue #skip to next year

        # gap in range detected!
        if possible_range_end:
            # complete the range that was in-progress & clear
            output += '-'+str(possible_range_end)
            possible_range_end = None
        # start new range (or single-year)
        output += ', '+str(year)
        continue
    #scan complete: ..check if an incomplete range was being assembled
    if possible_range_end:
        output += '-'+str(possible_range_end)
    return output

def get_connection( db_url=None, connection_func=None, sqlalchemy_echo=True):
    """
    utility function, to assist in obtaining connections to the warehouse

    Keyword Parameters:
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)
    sqlalchemy_echo  --  Boolean, representing if SQLAlchemy generated SQL
      should be output to stdout for debugging purposes (Default: True)

    Exceptions:
    ConnectionMissingArgument  -- raised if neither connection or db_url parameter
      is specified.

    >>> get_connection() #no connection details
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    if connection_func is None:
        # try fallback: create a connection from url
        if db_url is None:
            raise ConnectionMissingArgument()
        try:
            connection = sqlalchemy.create_engine(db_url,echo=sqlalchemy_echo).connect()
            return connection
        except:
            raise
    connection = connection_func()
    return connection

def get_roles( associations):
    """
    returns three lists representing detected Dimension roles

    Dimensional roles are OLAP dimension tables referenced in
    additional ways with different meanings. E.g.: fact#date_dim_id [
    dimensional reference], fact$start_date_dim_id [additional
    reference to date_dim using a "starting time" role.]

    Keyword Parameters:
    associations  -- list of table relation DTOs representing potential
        lookups against one or more Roles.

    Returns:
    3tuple comprising 1) a list table DTOs for new 'Roles' 2) Dict of
        'role-ified' assocation DTO to replace initial table references
        , indexed by ('table_name', 'table_column') tuples.
        3) list of additional association DTOs relating the new Roles
        to their base Dimensions.

    >>> from pprint import pprint
    >>> no_roles = [ {'parent': 'bar_dim', 'parent_column': 'bar_whid'
    ...               , 'table': 'foo_fact', 'column': 'bar_whid'
    ...               , 'type':'fact dimension'}]
    >>> get_roles( no_roles)
    ([], {}, [])
    >>> one_role = no_roles + [{'parent': 'bar_dim'
    ...                        , 'parent_column': 'bar_whid'
    ...                        , 'table': 'foo_fact'
    ...                        , 'column': 'special_use_bar_whid'
    ...                        , 'type':'fact dimension'}]
    >>> roles = get_roles( one_role)
    >>> role_tables, fact_relations, role_relations = roles
    >>> pprint( role_tables)
    [{'name': 'special_use_bar_dim',
      'project': None,
      'rows': None,
      'type': 'dimension role',
      'updated': None,
      'years': None}]
    >>> pprint( fact_relations)
    {('foo_fact', 'special_use_bar_whid'): {'column': 'special_use_bar_whid',
                                            'parent': 'special_use_bar_dim',
                                            'parent_column': 'bar_whid',
                                            'table': 'foo_fact',
                                            'type': 'fact dimension role'}}
    >>> pprint( role_relations)
    [{'column': 'bar_whid',
      'parent': 'bar_dim',
      'parent_column': 'bar_whid',
      'table': 'special_use_bar_dim',
      'type': 'dimension role base'}]
    """
    role_tables_by_name = {}
    relations_by_table_column_tuple = {}
    new_associations = []
    unparseable_role_associations = []
    for table_association in associations:
        parent_column = table_association['parent_column']
        parent_table = table_association['parent']
        column = table_association['column']
        association_type = table_association['type']
        type_role_lookup = 'fact dimension role'
        if ( (not parent_column == column)
                and (not association_type == type_role_lookup) ):
            # fact dimension is likely a Role (aliased dimension)
            # fact field format: "purpose_of_role_{pkey_column_from_base_dim}"
            try:
                role_prefix, split_remainder = column.split( parent_column)
            except ValueError:
                bad = table_association
                unparseable_role_associations.append( bad)
                msg = "unable to determine Role name for association: {}"
                logging.info(DimensionRoleError(msg.format(bad)), exc_info=True)
                continue #skip further processing of the association
            # make new name for role, using the prefix
            role_name = role_prefix + parent_table
            # make an updated relation & add to replacement associations list
            replacement_relation = deepcopy(table_association)
            replacement_relation['type'] = type_role_lookup
            replacement_relation['parent'] = role_name
            key = (replacement_relation['table'], column)
            relations_by_table_column_tuple[key] = replacement_relation
            if role_name not in role_tables_by_name:
                # add a new Dimension Roles
                new_role = {'name': role_name
                            ,'type': 'dimension role', 'years': None
                            ,'updated': None, 'rows': None, 'project': None}
                role_tables_by_name[role_name] = new_role
                # and make a relation connecting the Role with its base Dim.
                role_relation = { 'table': role_name, 'parent': parent_table
                    ,'column': parent_column ,'parent_column': parent_column
                    ,'type': 'dimension role base'}
                new_associations.append( role_relation)
    role_tables = list( role_tables_by_name.values())
    assert len(role_tables) == len(new_associations) #exactly 1x assoc per Role
    return role_tables, relations_by_table_column_tuple, new_associations

def get_table_bounds_tuple(table):
    """
    returns 4tuple of floats representing North,East,South,West bounds

    bounds represent decimal degrees latitude/longitude (inclusive)

    Keyword Parameters:
    table  -- Dictionary, representing current a DWSupport data table

    >>> test_table1 = {'bounds': 'None'}
    >>> get_table_bounds_tuple(test_table1) #Expect nothing
    >>> test_table2 = {'bounds': '59.9, None, 75, None'}
    >>> get_table_bounds_tuple(test_table2)
    (59.9, None, 75, None)
    >>> test_table3 = {'bounds': '60, -99.99, 75.0, -140'}
    >>> get_table_bounds_tuple(test_table3)
    (60, -99.99, 75.0, -140)
    """
    bounds_tuple = ast.literal_eval(table['bounds'])
    return bounds_tuple

def get_table_spatial_bounds(dwsupport_model, source_api_id, data_header, data):
    """
    returns 4tuple of floats representing North,East,South,West bounds

    bounds represent decimal degrees latitude/longitude (inclusive)

    Keyword Parameters:
    dwsupport_model  -- Dictionary, representing current DWSupport conf.
    source_api_id  -- String, representing the API id of dataset to
      return bounds for.
    data_header  -- list of strings, representing field names for each
      ordinal position in a 'data' row.
    data  -- collection of collections, representing the minimal rows of
      data from 'source_api_id' neccessary to determine spatial bounds

    >>> api_id = 'my.test_fact'
    >>> p1 = {'name': 'my'}
    >>> p2 = {'name': 'warehouse'}
    >>> fact1 = {'name': 'test_fact', 'project': p1['name']}
    >>> dim1 = {'name': 'latitude_dim', 'project': p2['name']}
    >>> dim2 = {'name': 'longitude_dim', 'project': p2['name']}
    >>> lookup1 = { 'table': fact1['name'], 'parent': dim1['name']
    ...            ,'type': 'fact dimension','column': 'latitude_dim_id'
    ...            ,'parent_column': 'latitude_dim_id'}
    >>> lookup2 = { 'table': fact1['name'], 'parent': dim2['name']
    ...            ,'type': 'fact dimension','column': 'longitude_dim_id'
    ...            ,'parent_column': 'longitude_dim_id'}
    >>> v1 = {'column': 'long', 'table': 'longitude_dim'}
    >>> v2 = {'column': 'lat', 'table': 'latitude_dim'}
    >>> m = { 'tables': [fact1, dim1]
    ...      ,'projects': [p1, p2]
    ...      ,'assocations': [lookup1, lookup2]
    ...      ,'variables': [v1, v2]
    ... }
    >>> header = ['longitude_dim$long', 'latitude_dim$lat']
    >>> data = [ [-101.0, 80.8]
    ...         ,[-110.1, 77.7]] #a single NE point + single SW point
    >>> get_table_spatial_bounds(m, api_id, header, data)
    (80.8, -101.0, 77.7, -110.1)
    """
    # identify all spatial dimensions & the dimensional base it derives from
    spatial_dimension_names_by_base_dimension_name = {#TODO: derive from DWSupport model
        'latitude_dim': ['latitude_dim']
        ,'longitude_dim': ['longitude_dim']
    }
    # search all values, tracking the minima/maxima encountered
    north_bounds, east_bounds, south_bounds, west_bounds = (None,)*4
    base_dimension_names_by_data_column_names = {} #map data fields to base dimensions
    for base_dimension_name, spatial_dimension_names in spatial_dimension_names_by_base_dimension_name.items():
        # get all Variables belonging to the Base dimension
        base_dimension_fields = [v for v in dwsupport_model['variables']
                                 if v['table']==base_dimension_name]
        for spatial_dimension_name in spatial_dimension_names:
            column_names = [spatial_dimension_name+'$'+field['column']
                                for field in base_dimension_fields]
            for column_name in column_names:
                base_dimension_names_by_data_column_names[column_name] = base_dimension_name

    for row in data:
        for column_index, data_column_name in enumerate(data_header):
            base_dimension_name = base_dimension_names_by_data_column_names[data_column_name]
            value = row[column_index]
            if value is not None:
                if base_dimension_name == 'latitude_dim':
                    if north_bounds is None or (value > north_bounds):
                        north_bounds = value
                    if south_bounds is None or (value < south_bounds):
                        south_bounds = value
                    continue # column processed, go to next field            
                if base_dimension_name == 'longitude_dim':
                    if east_bounds is None or (value > east_bounds):
                        east_bounds = value
                    if west_bounds is None or (value < west_bounds):
                        west_bounds = value
           # column processed, go to next field
    # return global minima/maxima
    return north_bounds, east_bounds, south_bounds, west_bounds

def exec_base(dto_list, validate_func, statement, db_url=None, connection_func=None
              ,additional_binds=None):
    """
    utility function, to assist in running dto management SQL.

    Keyword Parameters:
    dto_list  --  list of dtos
    validate_func  -- a Boolean function for checking if dto is well formed
      (rases Exception if not well formed).
    statement  --  String, representing DML SQL statement to be used. Any
      bind variables must match the names of dto attributes (dto_list will be
      directly used as the SQLAlchemy execute binds list).
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)
    additional_binds  -- additional bind parameters, to be used for every DTO

    Exceptions:
    ExecMissingArgument  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when dto is not well formed
    SQLAlchemyError  -- raised when problems connecting to datastore occur.

    >>> empty_list = []
    >>> def validate( dto):\
       return True
    >>> sql1 = "Select 'foo'"
    >>> exec_base( empty_list, validate, sql1) #no connection details
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    >>> dtos = ['anything']
    >>> def validate_breaks( dto):\
       raise Exception("Always breaks!")
    >>> exec_base( dtos, validate_breaks, sql1, db_url="sqlite:///:memory:") #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ValidateException:
    """
    # check input (and add any additional/unvalidated bind values)
    execute_binds = []
    for dto in dto_list:
        try:
            validate_func( dto)
        except Exception as e:#TODO:all dto exception should share a base class
            e_type = type(e)
            msg = 'DTO validation failed ({}: "{}"): {}'.format(e_type, e, dto)
            raise ValidateException( msg ) from e
        add_attributes = deepcopy(dto)
        try: #if additional bind attributes were specified, add them to DTO
            for additional_key,add_this_value in additional_binds.items():
                add_attributes[additional_key] = add_this_value
        except AttributeError:
            pass # continue, without adding any additional bind attributes
        execute_binds.append( add_attributes)
    # get db connection
    try:
        connection = get_connection(db_url=db_url, connection_func=connection_func)
    except ConnectionMissingArgument as e:
        raise ExecMissingArgument(e)
    # execute SQL statement with binds
    try:
        connection.execute( statement, execute_binds)
    except:
        raise
    finally:
        connection.close()
