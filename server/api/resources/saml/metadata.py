"""
Module defining Falcon resource, for API's SAML2 Service Provider metadata

Copyright (C) 2017 ERT Inc.
"""
import falcon
from pyicam.saml.metadata import get_entity_descriptor

from api import config_loader

route = 'metadata'
"""
String representing the URI path for this endpoint

E.g., "/metadata"
"""

class EntityDescriptor:
    """
    Falcon resource object, representing the API's SAML Service Provider metadata 
    """

    def on_get(self, request, resp, **kwargs):
        """
        Falcon resource method, for handling HTTP request GET method

        Falcon request provides: parameters embedded in URL via a keyword args
        dict, as well as convenience class variables falcon.HTTP_*
        """
        settings_path = config_loader.get_server_file_path('settings.json')
        cert_path = config_loader.get_server_file_path('api/auth/saml-sp.crt')
        key_path = config_loader.get_server_file_path('api/auth/secrets/saml-sp.key')
        metadata, content_type = get_entity_descriptor(settings_path, cert_path, key_path)
        resp.content_type = content_type
        resp.body = metadata
