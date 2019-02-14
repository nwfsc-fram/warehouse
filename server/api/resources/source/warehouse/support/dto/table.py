"""
Module, providing a DAO api for accessing metadata on warehouse tables

Warehoused data is organized into sets of tables, representing measured facts
as well as different dimensional spaces the facts can be grouped by.

Copyright (C) 2016 ERT Inc.
"""
from datetime import datetime

import sqlalchemy

from api.resources.source.warehouse.support import dto_util
from api.resources.source.warehouse.support.dto import (
    table_type
   ,contact
   ,project
)

TABLE = "table"
# support table,containing the list of tables which constitute the warehouse

sql_bounds_fields = ('north_bound', 'east_bound', 'south_bound', 'west_bound')
# 4tuple representing names of table SQL fields for storing spatial bounds

class ValidateTypeError(TypeError):
    """
    Raised when type of a Warehouse metadata table is not Dict-like
    """
    pass
class ValidateMissingValue(ValueError):
    """
    Raised when a required, warehouse metadata Table attribute is absent.
    """
    pass
class ValidateUnexpectedValue(ValueError):
    """
    Raised when an unrecognized, warehouse Table attribute is encountered.
    """
    pass

def validate( table):
    """
    validate if referenced object conforms to this module's api for warehouse
    tables.

    Keyword Parameters:
    table -- dictionary representing a warehoused table.

    Exceptions:
    ValidateTypeError -- raised when table parameter is not a dictionary
    ValidateMissingValue -- raised when table parameter is incomplete
    ValidateUnexpectedValue -- raised when table parameter is malformed

    >>> import datetime
    >>> from copy import deepcopy
    >>> tab1 = { 'name':'catch_fact', 'type':'fact'
    ...         ,'updated': datetime.datetime(2016, 1, 1)
    ...         ,'rows': 999, 'project': 'FRAM Trawl Survey'
    ...         ,'contact': 'Name: Awesome Pat <a.pat@example.domain>'
    ...         ,'years': '1971-1972, 1989, 2016', 'selectable': True
    ...         ,'inport_id': None, 'description': None, 'uuid': None
    ...         ,'inport_replacement_project_id': None
    ...         ,'title': 'Survey Catch', 'update_frequency': 'continually'
    ...         ,'restriction': 'otherRestrictions', 'usage_notice': None
    ...         ,'keywords': None, 'bounds': '80.0, -110.5, 60.06, -134'
    ...         ,'confidential': False}
    >>> validate( tab1)
    True
    >>> validate( '{"column":"json_table"}')
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table.ValidateTypeError: <class 'str'>
    >>> partial = deepcopy(tab1); removed = partial.pop('updated')
    >>> validate( partial)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table.ValidateMissingValue: updated
    >>> extra = deepcopy(tab1); extra['shouldnt_be_here!'] = True
    >>> validate( extra)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.table.ValidateUnexpectedValue: shouldnt_be_here!
    """
    try:
        table_keys = table.keys()
    except AttributeError as e: #Error, table is not dict-like
        raise ValidateTypeError(type(table)) from e
    # verify object contents
    expected_keys = ['name','type','rows','updated','years','project','contact'
                     ,'selectable', 'inport_id', 'description', 'title', 'uuid'
                     ,'inport_replacement_project_id'
                     ,'update_frequency', 'restriction', 'usage_notice'
                     ,'keywords', 'bounds', 'confidential'
    ]
    for key in expected_keys: #check that *all* attributes are present
        if key not in table_keys:
            raise ValidateMissingValue( key)
    for key in table_keys: #check for any non-standard attributes
        if key not in expected_keys:
            raise ValidateUnexpectedValue( key)
    # must be good!
    return True

def _bounds_key_to_quartet(table):
    """
    Replaced bounds key in referenced dict with four directional keys

    >>> from pprint import pprint
    >>> tab1 = {'bounds': '-40.0, 55.5, -60.6, 70'}
    >>> _bounds_key_to_quartet(tab1)
    >>> pprint(tab1)
    {'east_bound': 55.5,
     'north_bound': -40.0,
     'south_bound': -60.6,
     'west_bound': 70}
    """
    bounds_N_E_S_W = dto_util.get_table_bounds_tuple(table)
    for index,key_name in enumerate(sql_bounds_fields): #N,E,S,W - in order
        table[key_name] = bounds_N_E_S_W[index]
    del table['bounds']

def _validate_and_split_bounds(table):
    """
    helper function to automatically perform specific post-validation change
    """
    validate(table)
    # parse 'bounds' into four separate fields
    _bounds_key_to_quartet(table)

def get( db_url=None, connection_func=None):
    """
    retrive the current list of tables from the warehouse support schema.

    Keyword Parameters:
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArgument  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> get()
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection( db_url, connection_func)
    # prepare statement, to get table metadata
    select_statement = ('SELECT \n'
                        '   t.name \n'
                        '  ,tt.type_name as type \n'
                        '  ,t.num_rows as rows \n'
                        '  ,t.aud_beg_dtm as updated \n'
                        '  ,t.data_years as years \n'
                        '  ,pt.name as project \n'
                        '  ,ct.info as contact \n'
                        '  ,t.is_selectable as selectable \n'
                        '  ,t.inport_entity_id as inport_id \n'
                        '  ,t.inport_replacement_project_id \n'
                        '  ,t.description \n'
                        '  ,t.title \n'
                        '  ,t.csw_uuid AS uuid \n'
                        '  ,tuf.iso_maintenance_update_code AS update_frequency \n'
                        '  ,tuc.gmd_code AS restriction \n'
                        '  ,t.usage_notice \n'
                        '  ,t.keywords \n'
                        '  ,t.north_bound \n'
                        '  ,t.east_bound \n'
                        '  ,t.south_bound \n'
                        '  ,t.west_bound \n'
                        '  ,t.is_sensitive as confidential \n'
                        'FROM {schema}.{table} t \n'
                        '   INNER JOIN {schema}.{type_table} tt \n'
                        '     ON t.table_type_id = tt.table_type_id \n'
                        '   INNER JOIN {schema}.{project_table} pt \n'
                        '     ON t.project_id = pt.project_id \n'
                        '   INNER JOIN {schema}.{contact_table} ct \n'
                        '     ON t.contact_id = ct.contact_id \n'
                        '   INNER JOIN {schema}.table_update_frequency tuf \n'
                        '     ON t.table_update_frequency_id = tuf.table_update_frequency_id \n'
                        '   INNER JOIN {schema}.table_use_constraint tuc \n'
                        '     ON t.table_use_constraint_id = tuc.table_use_constraint_id \n'
                       ).format(schema=dto_util.SCHEMA, table=TABLE
                                ,contact_table=contact.TABLE
                                ,type_table=table_type.TABLE
                                ,project_table=project.TABLE)
    try:
        result = connection.execute( select_statement)
        tables = list()
        for row in result:
            table = dict(row) #make a real dict, so we can pprint() etc.
            # condense SQL spatial bounds fields into a simple string
            sql_bounds_values = (table[field] for field in sql_bounds_fields)
            table['bounds'] = '{}, {}, {}, {}'.format(*sql_bounds_values)
            for key in sql_bounds_fields: #remove the SQL fields
                del table[key]
            validate(table)
            tables.append(table)
        return tables
    except:
        raise
    finally:
        connection.close()

def save(tables, db_url=None, connection_func=None):
    """
    persists a list of one (or more) tables, to the warehouse database

    Keyword Parameters:
    tables  --  list of tables
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
    # prepare statement, to write out the table metadata
    template = """INSERT into {schema}.{table} (
                   name
                  ,project_id
                  ,contact_id
                  ,data_years
                  ,table_type_id
                  ,aud_beg_dtm
                  ,is_selectable
                  ,inport_entity_id
                  ,inport_replacement_project_id
                  ,description
                  ,num_rows
                  ,title
                  ,csw_uuid
                  ,table_update_frequency_id
                  ,table_use_constraint_id
                  ,usage_notice
                  ,keywords
                  ,north_bound
                  ,east_bound
                  ,south_bound
                  ,west_bound
                  ,is_sensitive
                  ) values (
                   %(name)s --use the same key name, as the type dictionary
                  ,(SELECT project_id
                      FROM {schema}.{project_table}
                      WHERE name=%(project)s )
                  ,(SELECT contact_id
                      FROM {schema}.{contact_table}
                      WHERE info=%(contact)s )
                  ,%(years)s
                  ,(SELECT table_type_id
                      FROM {schema}.{type_table}
                      WHERE type_name=%(type)s  ) --again, use name of relevant key
                  ,%(updated)s
                  ,%(selectable)s
                  ,%(inport_id)s
                  ,%(inport_replacement_project_id)s
                  ,%(description)s
                  ,%(rows)s
                  ,%(title)s
                  ,%(uuid)s
                  ,(SELECT table_update_frequency_id
                      FROM {schema}.table_update_frequency
                      WHERE iso_maintenance_update_code=%(update_frequency)s )
                  ,(SELECT table_use_constraint_id
                      FROM {schema}.table_use_constraint
                      WHERE gmd_code=%(restriction)s )
                  ,%(usage_notice)s
                  ,%(keywords)s
                  ,%(north_bound)s
                  ,%(east_bound)s
                  ,%(south_bound)s
                  ,%(west_bound)s
                  ,%(confidential)s
                  )"""
    insert_statement = template.format(schema=dto_util.SCHEMA, table=TABLE
                                       ,type_table=table_type.TABLE
                                       ,project_table=project.TABLE
                                       ,contact_table=contact.TABLE
                                      )
    # postgresql can't insert NULL into non-null fields (even with defaults)
    for t in tables:
        if t['rows'] is None:
            t['rows'] = -1 # rows: Table might not even exist, yet
        if t['updated'] is None:
            t['updated'] = datetime.now() #multiple insert statements is too hard
        if t['project'] is None:
            t['project'] = 'warehouse' # DB default, is to use the warehouse
        if t['contact'] is None:
            t['contact'] = 'Name: FRAM Data Team <nmfs.nwfsc.fram.data.team@noaa.gov>'
        if t['update_frequency'] is None:
            t['update_frequency'] = 'continual'
    # insert! -- directly use tables dictionaries for binds
    dto_util.exec_base( tables, _validate_and_split_bounds, insert_statement, db_url=db_url
                       ,connection_func=connection_func)

def update_by_name(name, table, db_url=None, connection_func=None):
    """
    updates a table (identified by name) in the warehouse database

    Keyword Parameters:
    name  -- String, name of the table to update
    table  --  Dict, representing the new table values (May change the name!)
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> import datetime
    >>> tab1 = { 'name':'catch_fact', 'type':'fact'
    ...         ,'updated': datetime.datetime(2016, 1, 1)
    ...         ,'rows': 999, 'project': 'FRAM Trawl Survey'
    ...         ,'contact': 'Name: Awesome Pat <a.pat@example.domain>'
    ...         ,'years': '1971-1972, 1989, 2016', 'selectable': True
    ...         ,'inport_id': None, 'description': None, 'uuid': None
    ...         ,'inport_replacement_project_id': None
    ...         ,'title': 'Survey Catch', 'update_frequency': 'continually'
    ...         ,'restriction': 'otherRestrictions', 'usage_notice': None
    ...         ,'keywords': None, 'bounds': '80.0, -110.5, 60.06, -134'
    ...         ,'confidential': False}
    >>> update_by_name('any_table', tab1)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # prepare statement, to update table metadata
    template = """UPDATE {schema}.{table} SET
                     name = %(name)s
                    ,data_years = %(years)s
                    ,table_type_id = (SELECT table_type_id
                                      FROM {schema}.{type_table}
                                      WHERE type_name=%(type)s  )
                    ,num_rows = %(rows)s
                    ,project_id = (SELECT project_id
                                   FROM {schema}.{project_table}
                                   WHERE name=%(project)s  )
                    ,contact_id = (SELECT contact_id
                                   FROM {schema}.{contact_table}
                                   WHERE info=%(contact)s  )
                    ,aud_beg_dtm = CURRENT_TIMESTAMP
                    ,is_selectable = %(selectable)s
                    ,inport_entity_id = %(inport_id)s
                    ,inport_replacement_project_id = %(inport_replacement_project_id)s
                    ,description = %(description)s
                    ,title = %(title)s
                    ,csw_uuid = %(uuid)s
                    ,table_update_frequency_id = (
                      SELECT table_update_frequency_id
                      FROM {schema}.table_update_frequency
                      WHERE iso_maintenance_update_code=%(update_frequency)s )
                    ,table_use_constraint_id = (SELECT table_use_constraint_id
                                                FROM {schema}.table_use_constraint
                                                WHERE gmd_code=%(restriction)s )
                    ,usage_notice = %(usage_notice)s
                    ,keywords = %(keywords)s
                    ,north_bound = %(north_bound)s
                    ,east_bound = %(east_bound)s
                    ,south_bound = %(south_bound)s
                    ,west_bound = %(west_bound)s
                  WHERE name = %(arg_table_name)s """
    update_statement = template.format(schema=dto_util.SCHEMA, table=TABLE
                                       ,type_table=table_type.TABLE
                                       ,project_table=project.TABLE
                                       ,contact_table=contact.TABLE
                                      )
    # update! -- directly use tables dictionary for binds
    dto_util.exec_base( [table], _validate_and_split_bounds, update_statement, db_url=db_url
                       ,connection_func=connection_func
                       ,additional_binds={'arg_table_name': name})
