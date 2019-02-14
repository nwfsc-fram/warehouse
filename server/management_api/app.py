"""
Module defining a WSGI application 'app', implementing the Warehouse management API

Copyright (C) 2017 ERT Inc.
"""
from types import SimpleNamespace

import falcon

import api
from api.handlers import middleware
from api.resources import p3p
from management_api.resources import (
   dump
  ,table
  ,usage_info
  ,variables
)

app = falcon.API( after=[middleware.crossdomain, middleware.p3p_header])

# add Exception handlers
app.add_error_handler(Exception, api.app_module.handle_http_error)

# map RESTful resources, to the URIs

app.add_route(api.app_module.get_uri_template(dump.route), dump.Dump())
app.add_route( api.app_module.get_uri_template('dump')
              ,dump.DumpDefaultFormat() # redirect 'dump' & 'dump/' to: 'dump/py'
)
app.add_route(api.app_module.get_uri_template(table.route), table.Copy())
app.add_route(api.app_module.get_uri_template(variables.route), variables.Variables())
app.add_route(api.app_module.get_uri_template(usage_info.route), usage_info.Help())
app.add_route(api.app_module.get_uri_template(p3p.str_route), p3p.PolicyReferenceFile())

# add request middleware
app = api.app_module.wrap_app_with_session_middleware(app) #share the primary Warehouse API sessions/cookies

