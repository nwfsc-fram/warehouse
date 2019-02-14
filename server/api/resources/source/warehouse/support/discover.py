"""
Module providing Data Access Object api to discover Warehouse metadata.

Metadata describes the structure and contents of the datawarehouse, enabling
access to the contained data.

Copyright (C) 2016 ERT Inc.
"""
from api.resources.source.warehouse.support.dto import (
     association
    ,table
)
from api.resources.source.warehouse.support import dto_util

SCHEMA = 'dw'
# Name of the schema containing the Warehouse tables

def lookup_tables( table_names, table_type='fact', lookup_type='dimension'
       , db_url=None, connection_func=None):
    """
    Utility function,returning table dictionaries associated with named tables.

    Keyword Parameters:
    table_names  --  A collection of Strings representing tables for which
      lists of associated tables are to be retrieved.
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArguments  -- raised if neither connection or db_url
      parameter is specified.

    >>> any_list = ['any_thing']
    >>> lookup_tables( any_list)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection(db_url, connection_func)
    # select table info
    select_statement = """
SELECT
   t_base.table_name as "table" --fact table name
  --,c.conkey
  ,a_base.attname as "table_field" --fact table field containing keys to be looked up
  ,t_ref.table_schema as "ref_table_schema" --schema of referenced dimension table
  ,t_ref.table_name as "ref_table"  --referenced dimension table name
  --,c.confkey
  ,a_ref.attname as "ref_table_field" --dimension column containing the keys
  ,pg_catalog.pg_get_constraintdef(c.oid, true) as condef  --pretty constraint text
FROM pg_catalog.pg_constraint c
  inner join information_schema.tables t_base
    on c.conrelid = (t_base.table_schema||'."'||t_base.table_name||'"')::regclass
  inner join pg_attribute a_base
    on c.conrelid = a_base.attrelid
    AND a_base.attnum = ANY(c.conkey)
  inner join information_schema.tables t_ref
    on c.confrelid = (t_ref.table_schema||'."'||t_ref.table_name||'"')::regclass
  inner join pg_attribute a_ref
    on c.confrelid = a_ref.attrelid
    AND a_ref.attnum = ANY(c.confkey)
WHERE c.contype = 'f' --Get only FOREIGN key constraints
  and t_base.table_name = %s
    """
    try:
        # build list of table dicts
        tables = []
        for name in table_names:
            result = connection.execute( select_statement, name)
            ref_table_encountered = [] #track each referenced table we add
            for row in result:
                ref_table = row['ref_table']
                if ref_table not in ref_table_encountered:
                    new_table = {'name': ref_table, 'type': lookup_type
                                 ,'updated':None, 'rows':None, 'years':None
                                 ,'project': None, 'contact': None
                                }
                    table.validate( new_table)
                    tables.append( new_table)
                    ref_table_encountered.append( ref_table) #only build 1x dict ea
        # check for Dimensional aliases (Roles)
        table_associations = lookup_associations(
            table_names
            ,db_url
            ,connection_func=connection_func
            ,lookup_roles=False)
        roles_tuple = dto_util.get_roles( table_associations)
        role_tables, replacement_associations, role_associations = roles_tuple
        if replacement_associations:
            # include Dimension"roles" as tables,upon detection of"role" assoc.
            tables.extend( role_tables)
        return tables
    except:
        raise
    finally:
        connection.close()

def lookup_associations( table_names, db_url=None, connection_func=None
        ,default_type='fact dimension', lookup_roles=True):
    """
    Utility function,returning association dictionaries associated with named tables.

    Keyword Parameters:
    table_names  --  A collection of table names, for which the table
      associations are to be retrieved.
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)
    default_type  -- String representing the association_type to be
      used for items found to be associated with one of the input tables
    lookup_roles  -- Boolean flag, indicating if the detected associations should
      be inspected for Dimensional aliases (Default: True)

    Exceptions:
    ConnectionMissingArguments  -- raised if neither connection or db_url
      parameter is specified.

    >>> any_list = ['any_thing']
    >>> lookup_associations( any_list)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection(db_url, connection_func)
    # retrieve associations
    select_statement = ('SELECT \n'
                        '   t_base.table_name as "table" --table name \n'
                        '  --,c.conkey \n'
                        '  ,a_base.attname as "table_field" --table field containing keys to be looked up \n'
                        '  ,t_ref.table_schema as "ref_table_schema" --schema of referenced table \n'
                        '  ,t_ref.table_name as "ref_table"  --referenced table name \n'
                        '  --,c.confkey \n'
                        '  ,a_ref.attname as "ref_table_field" --referenced table column containing the keys \n'
                        '  ,pg_catalog.pg_get_constraintdef(c.oid, true) as condef  --pretty constraint text \n'
                        'FROM pg_catalog.pg_constraint c \n'
                        '  inner join information_schema.tables t_base \n'
                      '''    on c.conrelid = (t_base.table_schema||'."'||t_base.table_name||'"')::regclass \n'''
                        '  inner join pg_attribute a_base \n'
                        '    on c.conrelid = a_base.attrelid \n'
                        '    AND a_base.attnum = ANY(c.conkey) \n'
                        '  inner join information_schema.tables t_ref \n'
                      '''    on c.confrelid = (t_ref.table_schema||'."'||t_ref.table_name||'"')::regclass \n'''
                        '  inner join pg_attribute a_ref \n'
                        '    on c.confrelid = a_ref.attrelid \n'
                        '    AND a_ref.attnum = ANY(c.confkey) \n'
                      '''WHERE c.contype = 'f' --Get only FOREIGN key constraints \n'''
                        '  and t_base.table_name = %s \n')
    try:
        # build list of association dicts
        associations = []
        for name in table_names:
            result = connection.execute( select_statement, name)
            for row in result:
                ref_table, ref_field = row['ref_table'], row['ref_table_field']
                table, field = row['table'], row['table_field']
                new_association = { 'parent':ref_table
                                   ,'parent_column': ref_field
                                   ,'table': table, 'column': field
                                   ,'type': default_type}
                association.validate( new_association)
                associations.append( new_association)
        if lookup_roles: # check for Dimensional aliases (Roles)
            roles_tuple = dto_util.get_roles( associations)
            role_tables, replacement_associations, role_associations = roles_tuple
            if replacement_associations:
                # prepare a map,to replace detected assoc w/new role-aware versions
                detected_assocs_by_table_column_tuple = {}
                for detected_association in associations:
                    detected_table = detected_association['table']
                    detected_column = detected_association['column']
                    key = (detected_table,detected_column)
                    detected_assocs_by_table_column_tuple[key]=detected_association            
                for key in replacement_associations.keys():
                    # replace naive assoc.s with Dimension "role"-aware versions
                    replacement = replacement_associations[key]
                    detected_assocs_by_table_column_tuple[key] = replacement
                associations = list(detected_assocs_by_table_column_tuple.values())
                # add additional associations,relating the detected Dimension
                #"roles" back to their base dimensions.
                associations.extend( role_associations)
        return associations
    except:
        raise
    finally:
        connection.close()
