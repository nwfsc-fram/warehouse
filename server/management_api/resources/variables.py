"""
Python module, defining a Falcon endpoint for DWSupport column managment

Copyright (C) 2017 ERT Inc.
"""
import falcon

import api.json as json
from api.resources.source import (
     source
)
from api.resources.source.selection import selection
from api.resources.source.warehouse import (
     warehouse
    ,util
)
from api.resources.source.warehouse.support import (
     configure
    ,dto
)
from api.resources.source.warehouse.support.model import model
from api.auth import auth
from . import auth as management_auth

route = 'table/{source_id}/variables'

class Variables():
    """
    Falcon resource object providing DWSupport column managment
    """

    def on_get(self, request, resp, **kwargs):
        """
        return JSON representing referenced table's associated columns
        """
        session_user = auth.get_user_id(request)
        with warehouse.get_source_model_session() as dwsupport_model:
            if not management_auth.is_management_permitted( session_user
                                                           ,dwsupport_model):
                msg = 'Warehouse management not authorized'
                raise falcon.HTTPUnauthorized(title='401', description=msg)
            #else
            sources = source.SourceUtil.get_list_of_data_sources(
                 request.url
                ,auth.get_user_id(request)
                ,dwsupport_model)
            requested_source_id = selection.get_requested_dataset_id(
                 sources
                ,request
                ,resp
                ,kwargs
            )
            rows_for_management_app = get_variable_identifier_queries_dicts(
                 requested_source_id
                ,dwsupport_model)
            resp.body = json.dumps(
                 { 'variables': rows_for_management_app }
                ,indent='\t'
            )
            return

    def on_post(self, request, resp, **kwargs):
        """
        Create/update table column, associated with referenced source_id

        TODO: add a JSON response body,compatible with DataTables Editor
        TODO2: improve documentation, unit test coverage
        """
        session_user = auth.get_user_id(request)
        with warehouse.get_source_model_session() as dwsupport_model:
            if not management_auth.is_management_permitted( session_user
                                                           ,dwsupport_model):
                msg = 'Warehouse management not authorized'
                raise falcon.HTTPUnauthorized(title='401', description=msg)
            #else
            sources = source.SourceUtil.get_list_of_data_sources(
                 request.url
                ,auth.get_user_id(request)
                ,dwsupport_model)
            requested_source_id = selection.get_requested_dataset_id(
                 sources
                ,request
                ,resp
                ,kwargs
            )
            source_project, source_table = requested_source_id.split('.') #TODO: refactor this
            # Add DTO variable (if needed)
            get_func = util.get_dwsupport_connection
            if request.params['action'] == 'create':
                table_name = request.params['data[0][table]']
                column_name = request.params['data[0][column]']
                python_type = request.params['data[0][python_type]']
                column_title = request.params['data[0][title]']
                variable_dto = { 'table': table_name
                                ,'column': column_name
                                ,'title': column_title
                                ,'python_type': python_type
                                ,'physical_type': None
                                ,'units': None
                                ,'max_length': None
                                ,'precision': None
                                ,'allowed_values': None
                                ,'description': None}
                dto.variable.save([variable_dto], connection_func=get_func)
            # get new default Queries this column should be in
            ## DataTables editor returns URLEncoded table,column defaults
            ## in format: data[{table_name}.{column_name}][defaults] = '{query1}(,{queryN})'
            key_prefix = 'data['
            key_suffix = '][column]'
            column_key_generator = (
                key for key in request.params
                if key.endswith(key_suffix)
            )
            column_key = next(column_key_generator)
            # get column details
            table_dot_column_plus_suffix = column_key[len(key_prefix):]
            table_dot_column = table_dot_column_plus_suffix[:len(key_suffix)*-1]
            table_name, column_name = table_dot_column.split('.')
            # get query details
            defaults_key = 'data[{}.{}][defaults]'.format(table_name,column_name)
            try:
                defaults_text = request.params[defaults_key]
                default_queries = {query.strip().lower() #parse text
                                   for query in defaults_text.split(',')}
            except KeyError as defaults_empty_or_missing:
                default_queries = set()
            query_variable_table = table_name
            # get table_name for a role
            association_key = 'data[{}.{}][association]'.format(table_name,column_name)
            try:
                association_column = request.params[association_key]
                association_dto = next(
                    (association for association
                     in dwsupport_model['associations']
                     if association['table'] == source_table
                     and association['column'] == association_column)
                )
                query_variable_table = association_dto['parent']
            except KeyError as association_empty_or_missing:
                pass # done. no able association is specified
            # update DTOs
            changes = dict() #track changes
            changes['add'] = list()
            changes['update'] = list()
            for query_name in default_queries:
                try:
                    # add column
                    query_dto = next(
                        (query for query in dwsupport_model['queries']
                         if query['name'] == query_name
                         and query['table'] == source_table)
                    )
                    try:
                        query_dto['variables'][table_name].append(column_name)
                    except KeyError as new_table:
                        query_dto['variables'][table_name] = [column_name]
                    dto.query.update_by_table_and_name(
                         source_table
                        ,query_name
                        ,query_dto
                        ,connection_func=get_func)
                    changes['update'].append(query_dto)
                except StopIteration as no_query_exists:
                    query_dto = { 'name': query_name
                                 ,'table': source_table
                                 ,'variables': { table_name: [column_name]}
                    }
                    dto.query.save([query_dto], connection_func=get_func)
                    changes['add'].append(query_dto)
            if default_queries == set():
                # remove column
                for query_dto in (query for query in dwsupport_model['queries']
                                  if query['table'] == source_table):
                    variable_tables = query_dto['variables'].keys()
                    if (query_variable_table in variable_tables
                            and column_name
                            in query_dto['variables'][query_variable_table]):
                        query_dto['variables'][query_variable_table].remove(column_name)
                        if len(query_dto['variables'][query_variable_table]) == 0:
                            del(query_dto['variables'][query_variable_table])
                        dto.query.update_by_table_and_name(
                             source_table
                            ,query_dto['name']
                            ,query_dto
                            ,connection_func=get_func)
                        changes['update'].append(query_dto)
            # JSON response per https://editor.datatables.net/manual/server
            msg = None
            if len(changes) == 0:
                msg = "No changes made"
            resp.body = json.dumps({'data': [changes], "error": msg})
            return

def get_variable_identifier_queries_dicts(source_id, dwsupport_model):
    """
    Return list of dicts, representing source_id's DWSupport columns

    Keyword Parameters:
    source_id  -- Sting, identifying the project table to return
      columns for
    dwsupport_model  -- Dict, representing current DWSupport schema

    >>> # Check return format
    >>> from pprint import pprint, pformat
    >>> test_source = 'trawl.catch_fact'
    >>> model = { 'tables': [ { 'name': 'catch_fact', 'type': 'fact'
    ...                        ,'project': 'trawl'}
    ...                      ,{ 'name': 'depth_dim', 'type': 'dimension'
    ...                        ,'project': 'warehouse'}
    ...                      ,{ 'name': 'operation_fact', 'type': 'fact'
    ...                        ,'project': 'acoustics'}]
    ...          ,'associations': [ { 'table': 'catch_fact'
    ...                              ,'column': 'catch_depth_whid'
    ...                              ,'parent': 'depth_dim'
    ...                              ,'type': 'fact dimension'}
    ...                            ,{ 'table': 'operation_fact'
    ...                              ,'column': 'op_depth_whid'
    ...                              ,'parent': 'depth_dim'
    ...                              ,'type': 'fact dimension'}]
    ...          ,'variables': [ { 'table': 'catch_fact'
    ...                           ,'column': 'retained_kg'}
    ...                         ,{ 'table': 'catch_fact'
    ...                           ,'column': 'retained_ct'}
    ...                         ,{ 'table': 'depth_dim'
    ...                           ,'column': 'meters'}
    ...                         ,{ 'table': 'depth_dim'
    ...                           ,'column': 'fathoms'}
    ...                         ,{ 'table': 'operation_fact'
    ...                           ,'column': 'frequency_mhz'}]
    ...          ,'variable_custom_identifiers': [
    ...               { 'id': 'freq', 'table': 'operation_fact'
    ...                ,'column': 'frequency_mhz'}]
    ...          ,'queries': [
    ...               {'name': 'core',
    ...                'table': 'catch_fact',
    ...                'variables': {'depth_dim': ['meters'],
    ...                              'catch_fact': ['retained_kg']}
    ...               }]
    ... }
    >>> out = get_variable_identifier_queries_dicts(test_source, model)
    >>> out.sort(key=pformat) #stabilize list order, for test
    >>> pprint(out)
    [{'association_column': 'catch_depth_whid',
      'queries': ['core'],
      'variable': {'column': 'meters', 'table': 'depth_dim'},
      'variable_custom_identifier': None},
     {'association_column': 'catch_depth_whid',
      'queries': [],
      'variable': {'column': 'fathoms', 'table': 'depth_dim'},
      'variable_custom_identifier': None},
     {'association_column': None,
      'queries': ['core'],
      'variable': {'column': 'retained_kg', 'table': 'catch_fact'},
      'variable_custom_identifier': None},
     {'association_column': None,
      'queries': [],
      'variable': {'column': 'retained_ct', 'table': 'catch_fact'},
      'variable_custom_identifier': None}]
    """
    data = list()

    # obtain query names (if any), for each column
    source_project, source_table = source_id.split('.') #TODO: refactor this
    query_names_by_table_column_tuple = _get_query_names_by_table_column_tuple(
         source_table
        ,dwsupport_model
    )
    # determine which tables are related to source_id
    related_tables = {association['parent']: association
                      for association
                      in dwsupport_model['associations']
                      if association['table'] == source_table}
    related_tables[source_table] = None #always relates to self
    # add details for each related table variables
    for related_table_name, association_dto in related_tables.items():
        physical_table = related_table_name # use name directly
        # unless an association exists
        if association_dto is not None:
            physical_table = association_dto['parent']
            # get physical table name for Dimension Role associations
            if association_dto['type'] == 'fact dimension role':
                physical_table_generator = (
                    a['parent'] for a
                    in dwsupport_model['associations']
                    if a['type'] == 'dimension role base'
                    and a['table'] == association_dto['parent']
                )
                physical_table = next(physical_table_generator)
        for variable_dto in (v for v
                             in dwsupport_model['variables']
                             if v['table'] == physical_table):
            # check for query names
            key = (related_table_name, variable_dto['column'])
            try:
                query_names = query_names_by_table_column_tuple[key]
            except KeyError:
                query_names = []
            # check for custom ID
            id_generator = (
                custom['id'] for custom
                in dwsupport_model['variable_custom_identifiers']
                if (custom['table'], custom['column']) == key
            )
            try:
                custom_id = next(id_generator)
            except StopIteration:
                custom_id = None
            association_column = None
            if association_dto is not None:
                association_column = association_dto['column']
            row = { 'queries': query_names
                   ,'variable': variable_dto
                   ,'association_column': association_column
                   ,'variable_custom_identifier': custom_id}
            data.append(row)
    return data


def _get_query_names_by_table_column_tuple(table_name, dwsupport_model):
    """
    Helper function,returns Dict representing query names

    Dict is indexed by tuples of (table, column) names for fields which
      belong to the listed queries

    Keyword Parameters:
    source_id  -- Sting, identifying the project table to return
      columns for
    dwsupport_model  -- Dict, representing current DWSupport schema

    >>> # Check return format
    >>> from pprint import pprint
    >>> test_table = 'catch_fact'
    >>> model = { 'tables': [ { 'name': 'catch_fact', 'type': 'fact'
    ...                        ,'project': 'trawl'}
    ...                      ,{ 'name': 'depth_dim', 'type': 'dimension'
    ...                        ,'project': 'warehouse'}
    ...                      ,{ 'name': 'operation_fact', 'type': 'fact'
    ...                        ,'project': 'acoustics'}]
    ...          ,'associations': [ { 'table': 'catch_fact'
    ...                              ,'parent': 'depth_dim'}
    ...                            ,{ 'table': 'operation_fact'
    ...                              ,'parent': 'depth_dim'}]
    ...          ,'variables': [ { 'table': 'catch_fact'
    ...                           ,'column': 'retained_kg'}
    ...                         ,{ 'table': 'catch_fact'
    ...                           ,'column': 'retained_ct'}
    ...                         ,{ 'table': 'depth_dim'
    ...                           ,'column': 'meters'}
    ...                         ,{ 'table': 'depth_dim'
    ...                           ,'column': 'fathoms'}
    ...                         ,{ 'table': 'operation_fact'
    ...                           ,'column': 'frequency_mhz'}]
    ...          ,'variable_custom_identifiers': [
    ...               { 'id': 'freq', 'table': 'operation_fact'
    ...                ,'column': 'frequency_mhz'}]
    ...          ,'queries': [
    ...               {'name': 'core',
    ...                'table': 'catch_fact',
    ...                'variables': {'depth_dim': ['meters'],
    ...                              'catch_fact': ['retained_kg']}
    ...               }]
    ... }
    >>> out = _get_query_names_by_table_column_tuple(test_table, model)
    >>> pprint(out)
    {('catch_fact', 'retained_kg'): ['core'], ('depth_dim', 'meters'): ['core']}
    """
    query_names_by_table_column_tuple = dict()
    for query in dwsupport_model['queries']:
        if query['table'] == table_name:
            query_name = query['name']
            for variable_table, columns in query['variables'].items():
                for variable_column in columns:
                    key = variable_table, variable_column
                    try:
                        query_names_by_table_column_tuple[key].append(query_name)
                    except KeyError:
                        query_names_by_table_column_tuple[key] = [query_name]
    return query_names_by_table_column_tuple
