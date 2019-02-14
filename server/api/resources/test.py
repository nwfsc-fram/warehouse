"""
Simple Python module, providing unittest discovery hook for doctest testcases

Copyright (C) 2015, 2016 ERT Inc.
"""
import unittest
import doctest

from api.resources import (
    p3p
    ,login
    ,logout
    ,usage_info
    ,user
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(p3p))
    tests.addTests(doctest.DocTestSuite(login))
    tests.addTests(doctest.DocTestSuite(logout))
    tests.addTests(doctest.DocTestSuite(usage_info))
    tests.addTests(doctest.DocTestSuite(user))
    return tests
