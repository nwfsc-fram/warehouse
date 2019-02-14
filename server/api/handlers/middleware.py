"""
Module providing Falcon web framework middleware 'handlers', for API

Copyright (C) 2016 ERT Inc.
"""
from urllib import parse

import api
from api.resources import p3p

base_url = api.config_loader.get_api_config()['proxy_url_base']

def crossdomain(req, resp):
    """
    Falcon middleware, enable Access-Control-Allow-Origin for Development

    TODO: provide a production configurable .ini flag
    """
    resp.set_header('Access-Control-Allow-Origin', '*')

def p3p_header(req, resp):
    """
    Falcon middleware,to insert P3P privacy policy info on each Response

    """
    api_ver = api.app_module.api_ver
    policy_url = _get_policy_reference_file_url(base_url, api_ver)
    resp.set_header('P3P', 'policyref="{}"'.format(policy_url))

def _get_policy_reference_file_url(url_base, api_version):
    """
    utility function, to construct URL pointing to Policy Reference File

    Per API requirement: SERVER_20

    >>> _get_policy_reference_file_url('http://some.domain/alias', 'v1')
    'http://some.domain/alias/api/v1/p3p.xml'
    >>> _get_policy_reference_file_url('http://some.domain/alias/', 'v1')
    'http://some.domain/alias/api/v1/p3p.xml'
    >>> _get_policy_reference_file_url('https://www.another.domain/proxy/path', 'v71')
    'https://www.another.domain/proxy/path/api/v71/p3p.xml'
    """
    # prepare a base URL
    base_with_no_trailing_slash = url_base.rstrip('/')
    base_with_target = base_with_no_trailing_slash+'/target'
    # prepare relative API path
    resource_route = p3p.str_route
    policy_ref_path = "api/{}/{}".format(api_version, resource_route)
    return parse.urljoin(base_with_target, policy_ref_path)
