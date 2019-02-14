"""
Module defining ResourceUtil class,providing functions useful to REST resources

Copyright (C) 2015, 2017 ERT Inc.
"""
import api #for api.app_module
from .resources import usage_info

__author__ = "Brandon Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

class ResourceUtil:
    """
    Base object, providing helper functions useful to all RESTful endpoints
    """

    @classmethod
    def get_request_url(self, wsgi_request, api_config):
        """
        Extracts the base URL for Source endpoint from referenced URL

        Keyword Parameters:
        wsgi_request  -- Object, representing HTTP request recieved by
          WSGI server
        api_config  -- Dict, representing API configuration options

        >>> import types
        >>> test_req1 = types.SimpleNamespace()
        >>> test_req1.url = None
        >>> conf = {'proxy_url_base': 'https://otherHost/warehouse/api'}
        >>> ResourceUtil.get_request_url(test_req1, conf) #Expect None (empty response)
        
        >>> test_req1.url = 'http://possible.proxy.domain/warehouse/api/v1/source/great.data/variables'
        >>> ResourceUtil.get_request_url(test_req1, conf)
        'https://otherHost/warehouse/api/v1/source/great.data/variables'
        """
        request_url = wsgi_request.url

        empty_name = '' #no endpoint
        known_component = api.app_module.get_uri_template(empty_name)
        # a known component of the URL, e.g.: "/v1/"

        try:
            request_base, found_known_path, extra_action = request_url.partition(
                known_component)
            # (check if string partition worked)
            msg = "Expected '{}' in API url: {}".format(known_component, request_url)
            assert known_component==found_known_path, msg
        except AttributeError as e:
            if request_url is None:
                return None #just return None
            raise e #otherwise, raise the unexpected exception

        configured_base = api_config['proxy_url_base']
        return configured_base + known_component + extra_action

    @classmethod
    def get_base_url(self, url):
        """
        Extracts API base URL from a referenced URL

        Keyword Parameters:
        url  -- String, representing an API URL of some
          kind (e.g.: http://host/api/v1/source,
          https://otherHost/warehouse/api/v1/source/great.data/variables)

        >>> test1 = None
        >>> ResourceUtil.get_base_url(test1) #expect None (empty) return

        >>> test2 = 'https://otherHost/warehouse/api/v1/source/great.data/variables'
        >>> ResourceUtil.get_base_url(test2)
        'https://otherHost/warehouse/api/v1/'
        """
        # Find the base URL where the API is being operated from

        empty_name = '' #no endpoint
        known_component = api.app_module.get_uri_template(empty_name)
        # a known component of the URL, e.g.: "/v1/"

        try:
            api_base, found_known_path, extra_action = url.partition(
                known_component)
            # (check if string partition worked)
            msg = "Expected '{}' in API url: {}".format(known_component, url)
            assert known_component==found_known_path, msg
        except AttributeError as e:
            if url is None:
                return None #just return None
            raise e #otherwise, raise the unexpected exception

        return api_base + known_component

    @classmethod
    def get_self_dict(self, url=None):
        """
        Returns a dict representing this REST resource.

        Keyword Arguments:
        url -- Url used to request this endpoint

        >>> d = ResourceUtil.get_self_dict()
        >>> len(d.keys())
        1
        >>> 'links' in d.keys()
        True
        >>> len(d['links']) == 2
        True
        >>> for link in d['links']:
        ...     if link['rel'] == 'self': link['href']

        >>> for link in d['links']:
        ...     if link['rel'] == 'help': link['href']
        'help'
        >>> d = ResourceUtil.get_self_dict('abc://efg.domain/api/v1/path/')
        >>> for link in d['links']:
        ...     if link['rel'] == 'self': link['href']
        'abc://efg.domain/api/v1/path/'
        >>> for link in d['links']:
        ...     if link['rel'] == 'help': link['href']
        'abc://efg.domain/api/v1/help'
        """
        dictResource = {}
        # add a minimum set of HATEOS relational links
        dictResource['links'] = []
        dictResource['links'].append({'rel' : 'self'
                                     ,'href': url})
        try:
            help_url = ResourceUtil.get_base_url(url) + usage_info.route
        except TypeError as e:
            if url is None:
                help_url = usage_info.route #just use the endpoint route
            else:
                raise e #otherwise, raise unexpected exception
        dictResource['links'].append({'rel' : 'help'
                                     ,'href': help_url})
        return dictResource
