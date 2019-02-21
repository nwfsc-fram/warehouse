"""
Module for classes providing a Metadata RESTful endpoint for Warehouse datasets

Copyright (C) 2015-2017, 2019 ERT Inc.
"""
import string

import api.json as json
import api.config_loader
from api.auth import auth
from api.resources.source import data
from api.resources.source.selection import (
     auth as selection_auth
    ,defaults
)
from api.resources.source.warehouse import warehouse, support
from api.resource_util import ResourceUtil
from api.resources.source.warehouse.support.dto import table

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "
__all__ = [
     'str_route'
    ,'Source'
    ,'SourceUti']

str_route = 'source'
#String representing the URI path for this endpoint

class Source:
    """
    Falcon resource, representing available Warehouse datasets
    """
    def on_get(self, request, resp):
        """
        Falcon resource method, for HTTP request method: GET

        Falcon request provides a request.url convenience instance variable
        """
        api_config = api.config_loader.get_api_config()
        request_url = SourceUtil.get_request_url(request, api_config)

        with warehouse.get_source_model_session() as model:
            sources = SourceUtil.get_list_of_data_sources(request_url, auth.get_user_id(request), model)
            # Build a dict, representing the Source RESTful entity/endpoint
            dictSource = SourceUtil.get_source( sources, request_url)
            str_nesting_indent_char = '\t'
            resp.body = json.dumps( dictSource, indent=str_nesting_indent_char)

class SourceUtil(ResourceUtil):
    """
    Utility type, encapsulating Source endpoint helper functions
    """

    str_property_indeterminate = 'NaN'
    #class variable, representing placeholder value for Source properties

    @classmethod
    def _table_to_metadata( self, table_to_convert, source_url, api_user_authorized, default_queries):
        """
        converts dwsupport Table into a Source item.

        Keyword Parameters:
        table_to_convert  -- DWSupport table dto providing source values
        source_url  -- full URL that was used to request the Source list
        api_user_authorized  -- Boolean, indicating if the current API
          session user is permitted to select data from referenced table
        default_queries  -- collection of Strings, representing the IDs
          of all default queries (e.g.: "core", "expanded") that are
          defined for this table

        >>> import datetime
        >>> from pprint import pprint
        >>> from copy import deepcopy
        >>> tab1 = { 'name':'catch_fact', 'type':'fact'
        ...         ,'updated': datetime.datetime(2014, 1, 1)
        ...         ,'rows': 99, 'project': 'warehouse'
        ...         ,'contact': 'Name: Anybody', 'inport_id': 7890
        ...         ,'inport_replacement_project_id': None
        ...         ,'years': '1971-1972, 1989, 2016', 'selectable': True
        ...         ,'description': None, 'uuid': None, 'confidential': False
        ...         ,'title': 'Survey Catch', 'update_frequency': 'continually'
        ...         ,'restriction': 'otherRestrictions', 'usage_notice': None
        ...         ,'keywords': None, 'bounds': '80.0, -110.5, 60.06, -134'}
        >>> test_source_url = 'https://Great.host/warehouse/api/v1/source'
        >>> test_authorized = True
        >>> test_defaults = {}
        >>> source = SourceUtil._table_to_metadata(tab1, test_source_url, test_authorized, test_defaults)
        >>> pprint( source) #use pretty-print,to stabilize dictionary key-order
        {'bounds': {'east-bound': -110.5,
                    'north-bound': 80.0,
                    'south-bound': 60.06,
                    'west-bound': -134},
         'contact': 'Name: Anybody',
         'defaults': None,
         'description': None,
         'id': 'warehouse.catch_fact',
         'is_selectable': True,
         'is_sensitive': False,
         'links': [{'href': 'https://Great.host/warehouse/api/v1/source/warehouse.catch_fact/selection.json',
                    'rel': 'json-selection'},
                   {'href': 'https://Great.host/warehouse/api/v1/source/warehouse.catch_fact/selection.csv',
                    'rel': 'csv-selection'},
                   {'href': 'https://Great.host/warehouse/api/v1/source/warehouse.catch_fact/selection.xlsx',
                    'rel': 'xlsx-selection'}],
         'name': 'catch_fact',
         'project': 'warehouse',
         'rows': 99,
         'selection_authorized': True,
         'title': 'Survey Catch',
         'updated': datetime.datetime(2014, 1, 1, 0, 0),
         'years': '1971-1972, 1989, 2016'}
        >>> # Check that non-confidential selection auth is always True
        >>> test_authorized2 = False
        >>> source = SourceUtil._table_to_metadata(tab1, test_source_url, test_authorized2, test_defaults)
        >>> source['selection_authorized']
        True
        >>> # Check that confidential selection auth is correctly shown
        >>> tab2 = deepcopy(tab1)
        >>> tab2['confidential'] = True
        >>> test_authorized3 = False
        >>> test_defaults2 = {"expanded", "core"}
        >>> source = SourceUtil._table_to_metadata(tab2, test_source_url, test_authorized3, test_defaults2)
        >>> source['selection_authorized']
        False
        >>> source['defaults']
        ['core', 'expanded']
        """
        table.validate(table_to_convert)
        table_name = table_to_convert['name']#FIXME: no title/label field available!
        table_project = table_to_convert['project']
        table_rows = table_to_convert['rows']
        table_updated = table_to_convert['updated']

        source_api_id = '.'.join( [table_project, table_name])

        select_authorized = True #Show non-confidential are always selectable
        if table_to_convert['confidential']:
            select_authorized = api_user_authorized #Show user-specific state

        #convert N,E,S,W bounds string to a dictionary
        north, east, south, west = support.dto_util.get_table_bounds_tuple(
            table_to_convert
        )
        bounds = {'north-bound': north, 'east-bound': east
            ,'south-bound': south, 'west-bound': west}

        queries = list(default_queries)
        queries.sort()
        if len(queries) < 1: #use NULL instead of an empty list
            queries = None
        source = { 'id': source_api_id
                  ,'name': table_name
                  ,'defaults': queries
                  ,'description': table_to_convert['description']
                  ,'project': table_project
                  ,'contact': table_to_convert['contact']
                  ,'rows' : table_rows
                  ,'is_selectable': table_to_convert['selectable']
                  ,'is_sensitive': table_to_convert['confidential']
                  ,'selection_authorized': select_authorized
                  ,'title': table_to_convert['title']
                  ,'years' : table_to_convert['years']
                  ,'updated' : table_updated
                  ,'bounds': bounds
                  ,'links': self._get_source_hateos_links(source_api_id, source_url)
                 }
        return source

    @classmethod
    def _get_warehouse_dict(self, num_expected_warehouse_rows=None, num_updated_time=None):
        """
        Helper method, returning a dict representing Public warehouse metadata

        >>> d = SourceUtil._get_warehouse_dict()
        >>> d['id']
        'warehouse'
        >>> isinstance( d['name'], str)
        True
        >>> isinstance( d['project'], str)
        True
        >>> d['defaults']
        
        >>> isinstance( d['description'], str)
        True
        >>> isinstance( d['contact'], str)
        True
        >>> d['rows']
        'NaN'
        >>> d['is_selectable']
        True
        >>> d['is_sensitive']
        False
        >>> d['selection_authorized']
        True
        >>> d['title']
        'NaN'
        >>> d['updated']
        'NaN'
        >>> d['years']
        'NaN'
        >>> d['bounds']
        'NaN'
        >>> d['links']
        'NaN'
        >>> len(d)
        15
        >>> num_warehouse_rows = 42
        >>> d = SourceUtil._get_warehouse_dict( num_warehouse_rows)
        >>> d['id']
        'warehouse'
        >>> isinstance( d['name'], str)
        True
        >>> isinstance( d['project'], str)
        True
        >>> d['defaults']
        
        >>> isinstance( d['description'], str)
        True
        >>> isinstance( d['contact'], str)
        True
        >>> d['rows']
        42
        >>> d['is_selectable']
        True
        >>> d['is_sensitive']
        False
        >>> d['selection_authorized']
        True
        >>> d['title']
        'NaN'
        >>> d['updated']
        'NaN'
        >>> d['years']
        'NaN'
        >>> d['bounds']
        'NaN'
        >>> d['links']
        'NaN'
        >>> len(d)
        15
        """
        dict_meta_data_warehouse = { 'id'     : warehouse.str_warehouse_id
                                   , 'name'   : warehouse.str_warehouse_name
                           ,'defaults': None
                           , 'description': warehouse.str_warehouse_description
                                   , 'project': warehouse.str_warehouse_project
                                   , 'contact': warehouse.str_warehouse_contact
                           , 'rows'     : SourceUtil.str_property_indeterminate
                           ,'is_selectable': True
                           ,'is_sensitive': False
                           ,'selection_authorized': True
                           ,'title': SourceUtil.str_property_indeterminate
                           ,'bounds': SourceUtil.str_property_indeterminate
                           ,'links': SourceUtil.str_property_indeterminate
                           , 'updated'  : SourceUtil.str_property_indeterminate
                           , 'years': SourceUtil.str_property_indeterminate #FIXME: populate this some how
        }
        if num_expected_warehouse_rows is not None:
            dict_meta_data_warehouse['rows'] = num_expected_warehouse_rows
        if num_updated_time is not None:
            dict_meta_data_warehouse['updated'] = num_updated_time
        return dict_meta_data_warehouse

    @classmethod
    def _get_source_hateos_links(self, source_api_id, source_url):
        """
        returns list of dicts, representing HATEOS links for a source

        HATEOS is a REST feature ("H(ypertext) A(s) (T)he E(ngine) O(f)
          S(tate)"), whereby the API is able to share with users how one
          requested object relates to other objects the user might be
          interested in.

        Keyword Parameters:
        source_api_id  -- String, representing the API id of a data set
        source_url  -- String representing the URL used by the user to
          request this "source" endpoint list of sources

        >>> from pprint import pprint
        >>> test_url = 'http://test.domain/api/v1/source'
        >>> links = SourceUtil._get_source_hateos_links('proj1.set1', test_url)
        >>> pprint(links)
        [{'href': 'http://test.domain/api/v1/source/proj1.set1/selection.json',
          'rel': 'json-selection'},
         {'href': 'http://test.domain/api/v1/source/proj1.set1/selection.csv',
          'rel': 'csv-selection'},
         {'href': 'http://test.domain/api/v1/source/proj1.set1/selection.xlsx',
          'rel': 'xlsx-selection'}]
        """
        # Find the base URL where the API is being operated from
        base_url = self.get_base_url(source_url)

        # Compose links
        hateos_links = [
            {'rel': 'json-selection'
             ,'href': '{}/{}/selection.json'.format(
                 base_url, source_api_id)}
            ,{'rel': 'csv-selection'
              ,'href': '{}/{}/selection.csv'.format(
                  base_url, source_api_id)}
            ,{'rel': 'xlsx-selection'
              ,'href': '{}/{}/selection.xlsx'.format(
                  base_url, source_api_id)}
        ]
        return hateos_links

    @classmethod
    def get_base_url(self, url):
        """
        Extracts the base URL for Source endpoint from referenced URL

        Keyword Parameters:
        url  -- String, representing an API source URL of some
          kind (e.g.: http://host/api/v1/source,
          https://otherHost/warehouse/api/v1/source/great.data/variables)

        >>> test1 = 'https://otherHost/warehouse/api/v1/source/great.data/variables'
        >>> SourceUtil.get_base_url(test1)
        'https://otherHost/warehouse/api/v1/source'
        """
        # add route, to the base URL where API is being operated from
        try:
            base_source_url = ResourceUtil.get_base_url(url) + str_route
        except TypeError as e:
            if url is None:
                return str_route #just return the endpoint route
            raise e #otherwise, raise unexpected exception

        return base_source_url

    @classmethod
    def get_list_of_data_sources(self, source_url, api_user_id, dwsupport_model, include_dims=True):
        """
        Returns a collection of dicts, representing available FRAM data sets

        Keyword Parameters:
        source_url  -- String, representing the URL used to request this
          list of sources
        include_dims  -- Boolean, indicating if warehoused Dimensions should be
            listed as data-sources, or if only warehoused 'cubes' (facts+joined
            dimensions) should be listed.
        api_user_id  -- String, representing unique ID for the user of
          the current API session.
        dwsupport_model  -- dictionary of lists, representing the
          DWSupport configuration.
        """
        list_of_dicts = []
        #Add data-sources configured via warehouse db
        tables = warehouse.get_source_tables()
        if not include_dims:
            tables_no_dims = [ t for t in tables if t['type'] == 'fact']
            tables = tables_no_dims
        request_urls = (source_url,)*len(tables) #same URL was used for all
        auths = [] # check table authorizations
        for table in tables:
            status = selection_auth.is_select_permitted(api_user_id, table, dwsupport_model)
            auths.append(status)
        default_queries = [] # retrieve table queries
        for table in tables:
            source_api_id = '.'.join( [table['project'], table['name']])
            queries = defaults.get_default_query_ids(source_api_id, dwsupport_model)
            default_queries.append(queries)
        db_sources = map(self._table_to_metadata, tables, request_urls, auths, default_queries) #convert tables
        list_of_dicts.extend( db_sources)
        # derive Warehouse metadata
        num_expected_warehouse_rows = 0
        num_updated_time = None
        for dict_meta_data in list_of_dicts:
            # set warehouse update time to the Greatest underlaying timestamp
            timestamp_set_updated = dict_meta_data['updated']
            if (num_updated_time is None) or (timestamp_set_updated > num_updated_time):
                num_updated_time = timestamp_set_updated
            # anticipate how many records the fused dataset will have
            num_expected_warehouse_rows += int(dict_meta_data['rows'])
        #Add the warehouse
        dict_warehouse = self._get_warehouse_dict(num_expected_warehouse_rows, num_updated_time)
        list_of_dicts.append(dict_warehouse)
        list_of_dicts.sort(key=lambda dataset:dataset['id']) #sort by source ID
        return list_of_dicts

    @classmethod
    def get_source( self, sources, str_url=None):
        """
        Returns a dict representing the Source endpoint

        Keyword Arguments:
        sources  --  list of metadata dictionaries representing data sets
        str_url -- Url used to request this endpoint

        >>> s = [ {'id': 'fake'} ] #close enough
        >>> d = SourceUtil.get_source( s)
        >>> len(d.keys())
        2
        >>> 'links' in d.keys()
        True
        >>> 'sources' in d.keys()
        True
        >>> len(d['links']) > 0
        True
        >>> d['sources']
        [{'id': 'fake'}]
        >>> for link in d['links']:
        ...     if link['rel'] == 'self': link['href']

        >>> url1 = 'abc://efg.domain/path/api/v1/source/foo.data/variables'
        >>> d = SourceUtil.get_source( s, url1)
        >>> for link in d['links']:
        ...     if link['rel'] == 'self': link['href']
        'abc://efg.domain/path/api/v1/source/foo.data/variables'
        >>> for link in d['links']:
        ...     if link['rel'] == 'help': link['href']
        'abc://efg.domain/path/api/v1/help'
        """
        dictSources = ResourceUtil.get_self_dict(str_url)
        # add a set of available DataSources
        dictSources['sources'] = sources
        return dictSources
