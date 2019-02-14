"""
Module defining ManagementResourceUtil RESTful helper class

Copyright (C) 2017 ERT Inc.
"""
from api.resource_util import ResourceUtil
import api #for api.app_module

__author__ = "Brandon Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

class ManagementResourceUtil(ResourceUtil):
    """
    Object providing helper functions to all RESTful managment endpoints
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
        >>> conf = {'management.proxy_url_base': 'https://otherHost/warehouse/management_api'}
        >>> ManagementResourceUtil.get_request_url(test_req1, conf) #Expect None (empty response)
        
        >>> test_req1.url = 'http://possible.proxy.domain/warehouse/management_api/v1/dump'
        >>> ManagementResourceUtil.get_request_url(test_req1, conf)
        'https://otherHost/warehouse/management_api/v1/dump'
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

        configured_base = api_config['management.proxy_url_base']
        return configured_base + known_component + extra_action
