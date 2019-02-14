#!/bin/python3
"""
This module presents the Warehouse api WSGI app, to mod_wsgi as: 'application'

Copyright (C) ERT Inc.

To serve a WSGI app, mod_wsgi requires the app to be: 1) defined in a Python
module file, and 2) named 'application'.
For details, see: http://www.modwsgi.org/
"""
import wsgiApps

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

application = wsgiApps.getWsgiAppRestful()
