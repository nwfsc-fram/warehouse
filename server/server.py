#!/bin/python3
"""
This module is used to serve the Warehouse Static content and data Api via HTTP

Copyright (C) 2015, 2016 ERT Inc.

The Pylons 'Waitress' Wsgi server is used to host warehouse resources over HTTP
(see: http://waitress.readthedocs.org/en/latest )
"""
import waitress
import wsgiApps
import os
import configparser

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

if __name__ == '__main__':
    # serve our composed WSGI app via waitress (for settings, see server.ini)
    wsgiAppComposed = wsgiApps.getWsgiAppComposite()
    # open & parse Waitress config file (how to use auto-load via PasteConfig
    # is unclear)
    filename = 'server.ini'
    str_module_dir = os.path.dirname(__file__)
    str_path_to_config = os.path.join(str_module_dir, filename)
    config_parser = configparser.ConfigParser()
    config_parser.read( str_path_to_config)
    heading = 'server:main'
    dict_config = config_parser[ heading]
    waitress.serve( wsgiAppComposed
                  , host=dict_config['host']
                  , port=dict_config['port'])
