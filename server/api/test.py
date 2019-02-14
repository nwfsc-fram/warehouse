# pylint: disable=global-statement
"""
Module providing unittest test discovery hook for our Doctest testcases

Copyright (C) 2015, 2016 ERT Inc.
"""
import unittest
import doctest
from time import sleep

from api import app_module as app
from api import (
    config_loader
    ,aes
    ,json
    ,resource_util
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

pentaho_stopped = False

def app_stop_pentaho():
    """
    helper function, to stop the WSGI app's configured Carte server
    """
    global pentaho_stopped
    while all((app.pentaho_started, not pentaho_stopped)):
        if app.pentaho_controller.status():
            app.pentaho_controller.stop()
            pentaho_stopped = True
            return
        sleep(2)
    
def load_tests(loader, tests, ignore):
    """
    Expose Doctest testcases to unitest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    app_doctests = doctest.DocTestSuite(app)
    for app_doctest in app_doctests:
        app_doctest.addCleanup(app_stop_pentaho)
    tests.addTests(app_doctests)
    tests.addTests(doctest.DocTestSuite(config_loader))
    tests.addTests(doctest.DocTestSuite(aes))
    tests.addTests(doctest.DocTestSuite(json))
    tests.addTests(doctest.DocTestSuite(resource_util))
    return tests
