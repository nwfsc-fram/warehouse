"""
Package defining a WSGI application 'app', implementing the Warehouse management API

Copyright (C) 2017 ERT Inc.
"""
from . import app as app_module #alias app Module, for intra-package use
from .app import app

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov> "
