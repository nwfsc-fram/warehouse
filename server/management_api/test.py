"""
Module providing unittest test discovery hook for our Doctest testcases

Copyright (C) 2017 ERT Inc.
"""
import unittest
import doctest

from . import app_module as app
from . import resource_util

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests(loader, tests, ignore):
    """
    Expose Doctest testcases to unitest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    app_doctests = doctest.DocTestSuite(app)
    tests.addTests(doctest.DocTestSuite(resource_util))
    return tests
