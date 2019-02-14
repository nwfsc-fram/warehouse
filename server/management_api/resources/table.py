"""
Python module, defining a Falcon endpoint to copy a DWSupport table

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
)
from api.resources.source.warehouse.support import configure
from api.resources.source.warehouse.support.model import model
from api.auth import auth
from . import auth as management_auth

route = 'table/{source_id}/copy'

class Copy():
    """
    Falcon resource object providing DWSupport table copy
    """
    allowed_methods = ['POST']

    def on_get(self, request, resp, **kwargs):
        """
        direct user to POST the login details
        """
        session_user = auth.get_user_id(request)
        with warehouse.get_source_model_session() as dwsupport_model:
            if not management_auth.is_management_permitted(session_user, dwsupport_model):
                msg = 'Warehouse management not authorized'
                raise falcon.HTTPUnauthorized(title='401', description=msg)

        allowed = self.allowed_methods
        msg = "GET method not allowed, Please POST new table parameters to 'copy'"
        raise falcon.HTTPMethodNotAllowed(allowed, description = msg)
        

    def on_post(self, request, resp, **kwargs):
        """
        Make copy of referenced DWSupport table, with specified changes
        """
        session_user = auth.get_user_id(request)
        with warehouse.get_source_model_session() as dwsupport_model:
            if not management_auth.is_management_permitted(session_user, dwsupport_model):
                msg = 'Warehouse management not authorized'
                raise falcon.HTTPUnauthorized(title='401', description=msg)
            #else
            sources = source.SourceUtil.get_list_of_data_sources(
                 request.url
                ,auth.get_user_id(request)
                ,dwsupport_model)
            requested_source_id = selection.get_requested_dataset_id(sources, request, resp, kwargs)
            try:
                new_table = request.params['name']
                new_project = request.params['project-name']
                new_variable_custom_identifiers = request.params['variable-custom-identifiers']
            except KeyError as error:
                raise falcon.HTTPBadRequest( #TODO: add functional test coverage
                        title="Missing Parameter"
                        ,description=(
                           "Unable to make copy of"
                           " data source: '{}'."
                           " (Copy request must specify HTTP POST parameter: {})"
                           ).format(requested_source_id, error))
            try:
                new_custom_ids_by_old_id = json.loads(new_variable_custom_identifiers)
            except json.json.scanner.JSONDecodeError as e:
                msg = ("Unable to make copy of"
                       " data source: '{}'."
                       " (Parameter is not valid JSON object: {})"
                      ).format(requested_source_id, e)
                raise falcon.HTTPInvalidParam(msg, 'variable-custom-identifiers')
            if type(new_custom_ids_by_old_id) != dict:
                msg = ("Unable to make copy of"
                       " data source: '{}'."
                       ' Parameter must be a JSON object: {{"existing_table_custom_variable_id": "new_id"}}'
                      ).format(requested_source_id)
                raise falcon.HTTPInvalidParam(msg, 'variable-custom-identifiers')
            try:
                new_dto_tuple = configure.copy_table(
                     requested_source_id
                    ,new_project
                    ,new_table
                    ,new_custom_ids_by_old_id
                )
                new_table, new_associations, new_variables, \
                new_variable_custom_identifiers, new_queries = new_dto_tuple
                resp.body = json.dumps(
                     { 'table': new_table, 'associations': new_associations
                      ,'variables': new_variables
                      ,'variable_custom_identifiers': new_variable_custom_identifiers
                      ,'queries': new_queries}
                    ,indent='\t'
                )
                return
            except configure.CopyTableUnsupportedTableType as e:
                raise falcon.HTTPBadRequest( #TODO: add functional test coverage
                        title="Bad Path"
                        ,description=("Copy only supported for tables of type"
                                      " 'fact'. (The '{}' data source in URL is"
                                      " type: '{}')"
                                     ).format(requested_source_id, e)
                )
            except configure.CopyTableDuplicateCopyName as e:
                msg = ("Unable to make copy of"
                       " data source: '{}'."
                       " (Please specify a new table name, a table with"
                       " the provided name already exists: {})"
                      ).format(requested_source_id, e)
                raise falcon.HTTPInvalidParam(msg, 'name')
            except configure.CopyTableNonuniqueVariableCustomIdentifiers as e:
                msg = ("Unable to make copy of"
                       " data source: '{}'."
                       " (The following new IDs must not duplicate any other"
                       " variable custom IDs: {})"
                      ).format(requested_source_id, e)
                raise falcon.HTTPInvalidParam(msg, 'variable-custom-identifiers')
            except configure.CopyTableMissingVariableCustomIdentifiers as e:
                msg = ("Unable to make copy of"
                       " data source: '{}'."
                       " (Copy request parameter must include new, unique"
                       " IDs for these existing variable custom IDs: {})"
                      ).format(requested_source_id, e)
                raise falcon.HTTPInvalidParam(msg, 'variable-custom-identifiers')
