"""
Module providing utility methods for instantiating Warehouse WSGI applications

Copyright (C) 2015-2017 ERT, Inc.
"""
import os
import logging

from werkzeug.wsgi import SharedDataMiddleware, DispatcherMiddleware
from werkzeug.exceptions import NotFound

from api.app import app as wsgiApp
from management_api.app import app as wsgiManagementApp

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

exceptionNullWsgiApp = NotFound
"""
Exception, to be used with Werkzeug as a stand-in for a null/empty WSGI app

per: http://werkzeug.pocoo.org/docs/0.10/middlewares
"""

def getWsgiAppRestful():
    #Returns a Wsgi app, serving our 'RESTful API' application
    logging.basicConfig(level=logging.INFO)
    return wsgiApp

def getWsgiManagementAppRestful():
    #Returns a Wsgi app, serving our 'RESTful Management API' app
    logging.basicConfig(level=logging.INFO)
    return wsgiManagementApp

def getWsgiAppStatic():
    #Returns a Wsgi app, serving static content from the project 'app/' folder
    stringPathToThisModule = os.path.dirname(__file__)
    stringPathToStaticContent = os.path.join( stringPathToThisModule, 'app')
    stringPathToManagementStaticContent = os.path.join(stringPathToThisModule, 'management_app')
    #Map static content to one or more URI's within this Wsgi application.
    stringStaticInternalUriPrefix = '/' #Don't prepend any internal prefix
    dictInternalPrefixToPathMapping = {
        stringStaticInternalUriPrefix: stringPathToStaticContent
       ,'/management': stringPathToManagementStaticContent
    }
    # instantiate a stand-alone Static content Wsgi app
    return SharedDataMiddleware( exceptionNullWsgiApp #make stand-alone
                               , dictInternalPrefixToPathMapping)

def getWsgiAppComposite():
    #Returns a 'dispatcher' Wsgi app, which glues two other Wsgi app together
    dictPathToWsgiAppMapping = {
         '': getWsgiAppStatic() #No path, serve content from the root
        ,'/api': getWsgiAppRestful()
        ,'/management_api': getWsgiManagementAppRestful()
    }
    # instantiate a stand-alone 'dispatcher' Wsgi app
    return DispatcherMiddleware( exceptionNullWsgiApp #No Wsgi app to wrap
                               , dictPathToWsgiAppMapping)
