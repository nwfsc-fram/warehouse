"""
Module defining Falcon resource, for API's SAML2 main, default endpoint

Copyright (C) 2017-2018 ERT Inc.
"""
from urllib.parse import urlparse
import logging

import falcon
import pyicam.saml.sso as saml

from api import (
    resource_util
    ,config_loader
)
from api.auth import auth

logger = logging.getLogger(__name__)

route = ''
"""
String representing the URI path for this endpoint

E.g., "/"
"""

def saml_assertion_to_ldap_style_name(assertion_attributes):
    """
    Return string, approximating a NOAA LDAP-style name for SAML user

    Keyword Parameters:
    assertion_attributes  -- Dict, representing SAML assertion
      attributes for a logged in user

    >>> test_attributes = {'mail': ['Pat.Ng@noaa.gov']}
    >>> saml_assertion_to_ldap_style_name(test_attributes)
    'uid=pat.ng,ou=People,o=noaa.gov'
    """
    # Adapt SAML user email assertion, into a LDAP-style name
    user_name, user_domain = assertion_attributes['mail'].pop().split('@')
    generated_ldap_id = 'uid={},ou=People,o={}'.format(user_name.lower(), user_domain)
    return generated_ldap_id

def get_url_host_port_path(proxy_base_path_url):
    """
    Return 3-tuple of strings, representing URL's host, port & path

    >>> get_url_host_port_path("https://nwcdevfram.nwfsc.noaa.gov/api")
    ('nwcdevfram.nwfsc.noaa.gov', '443', '/api')
    """
    parsed_url = urlparse(proxy_base_path_url)
    port = str(parsed_url.port)
    if parsed_url.port is None:
        port = '80'
        if parsed_url.scheme == 'https':
            port = '443'
    return parsed_url.hostname, port, parsed_url.path

class SamlEndpoint:
    """
    Falcon resource object, representing the API's SAML endpoint

    Endpoint provides two SP capabilities, specified by HTTP parameter:
     - AttributeConsumerService (Parameter: acs), e.g. user "login"
     - SingleLogoutService (Parameter: sls)
    """
    def on_post(self, request, resp, **kwargs):
        """
        Falcon resource method, for handling HTTP request POST method

        Falcon request provides: parameters embedded in URL via a keyword args
        dict, as well as convenience class variables falcon.HTTP_*
        """
        if request.query_string == 'acs':
            conf = config_loader.get_api_config()
            req_host, req_port, proxy_api_base = get_url_host_port_path(conf['proxy_url_base'])
            proxy_base, garbage = proxy_api_base.split('/api') #remove trailing "/api"
            req_path = proxy_base+request.env['SCRIPT_NAME']+request.env['PATH_INFO']
            settings_path = config_loader.get_server_file_path('settings.json')
            cert_path = config_loader.get_server_file_path('api/auth/saml-sp.crt')
            key_path = config_loader.get_server_file_path('api/auth/secrets/saml-sp.key')
            attributes = saml.login(req_host, req_port, req_path
                                    ,settings_path, cert_path, key_path
                                    ,post_data=request.params)

            generated_ldap_id = saml_assertion_to_ldap_style_name(attributes)

            auth.create_login_session( generated_ldap_id, request
                                      ,saml=attributes) #Indicate user is logged in
            if 'relay_state' in attributes:
                # Process the saml2 RelayState info like a redirect URL
                resp.status = falcon.HTTP_303 #See Other
                resp.set_header('Location', attributes['relay_state'])
            return #done
        # else
        for link_set in resource_util.ResourceUtil.get_self_dict(request.url)['links']:
            if link_set['rel'] == 'help':
                help_url = link_set['href']
                break
        raise falcon.HTTPInvalidParam(msg='See '+help_url, param_name='acs')

    def on_get(self, request, resp, **kwargs):
        """
        Falcon resource method, for handling HTTP request GET method

        Falcon request provides: parameters embedded in URL via a keyword args
        dict, as well as convenience class variables falcon.HTTP_*
        """
        if request.query_string == 'sls':
            raise falcon.HTTPInternalServerError(title='Unsupported', description='SAML single logout is not yet supported.')
        # else
        for link_set in resource_util.ResourceUtil.get_self_dict(request.url)['links']:
            if link_set['rel'] == 'help':
                help_url = link_set['href']
                break
        raise falcon.HTTPInvalidParam(msg='See '+help_url, param_name='sls')
