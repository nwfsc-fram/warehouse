"""
Package defining a WSGI application 'app', implementing the Warehouse API

Copyright (C) 2015, 2016 ERT Inc.
"""
from api import app as app_module #alias app Module, for intra-package use
from api.app import app

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov> "

# export only the Wsgi application Class.
__all__ = ['app']
