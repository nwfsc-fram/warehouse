"""
Module providing unittest test discovery hook for our Doctest testcases

Copyright (C) 2015, 2016 ERT Inc.
"""
import unittest
import doctest

from . import (
    selection
    ,streaming
    ,parameters
    ,defaults
    ,pivot
    ,auth
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite( selection))
    tests.addTests(doctest.DocTestSuite( parameters))
    tests.addTests(doctest.DocTestSuite(pivot))
    tests.addTests(doctest.DocTestSuite(defaults))
    tests.addTests(doctest.DocTestSuite(auth))
    tests.addTests(doctest.DocTestSuite(streaming))
    return tests
