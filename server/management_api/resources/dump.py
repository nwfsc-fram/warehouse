"""
Python module, defining a Falcon endpoint to dump current DWSupport config

Copyright (C) 2017 ERT Inc.
"""
from pprint import pformat

import falcon

import api.json as json
from api.resources.source.warehouse import (
     util
    ,warehouse
)
from api.resources.source.warehouse.support.model import model
from api import config_loader
from ..resource_util import ManagementResourceUtil
from api.auth import auth
from . import auth as management_auth

route = 'dump/{format}'

formats = ['py', 'json']

DWSUPPORT_CONFIG_HEADER = '''"""
Simple Python module defining the current DWSupport configuration

Copyright (C) 2016 ERT Inc.
"""
import datetime

'''

class Dump():
    """
    Falcon resource object providing DWSupport config dump
    """

    def on_get(self, request, resp, **kwargs):
        """
        respond with Python module representation of the current config
        """
        session_user = auth.get_user_id(request)
        with warehouse.get_source_model_session() as dwsupport_model:
            if not management_auth.is_management_permitted(session_user, dwsupport_model):
                msg = 'Warehouse management not authorized'
                raise falcon.HTTPUnauthorized(title='401', description=msg)
            #else
            requested_format = kwargs['format'].lower()
            if requested_format not in formats:
                msg = 'Dump format not found. Leave blank for Python (py) or include a supported format in dump URL: {}'.format(formats)
                raise falcon.HTTPNotFound(title='404', description=msg)
            #else
            if requested_format == 'py':
                conf_module_text = DWSUPPORT_CONFIG_HEADER
                conf_module_text += 'model = {}'.format(get_model_string())
                conf_module_text += '\n'
                resp.body = conf_module_text
                return
            if requested_format == 'json':
                resp.body = json.dumps({'model': dwsupport_model})
                return


class DumpDefaultFormat():
    """
    Falcon resource object providing redirect to dump/py
    """
    def on_get(self, request, resp):
        """
        respond with status HTTP 303 & default location
        """
        #use Proxy config, to generate an absolute URL for remote user
        api_config = config_loader.get_api_config()
        absolute_url = ManagementResourceUtil.get_request_url(request, api_config)
        absolute_url_base = ManagementResourceUtil.get_base_url(absolute_url)
        # build URL with the default format (.py), for dump
        default_url = absolute_url_base + 'dump/py'

        # redirect
        redirect = {'location': default_url}
        raise falcon.HTTPError('303 See Other', headers = redirect)

def get_model_string():
    """
    return string, representing the current DWSupport model
    """
    current = model.dump(connection_func=util.get_dwsupport_connection)
    return pformat(current, width=76)
