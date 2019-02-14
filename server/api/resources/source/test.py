"""
Module providing unittest test discovery hook, for our Doctest testcases

Copyright (C) 2015, 2016 ERT Inc.
"""
import unittest
import doctest

from api.resources.source import (
    source
    ,parameters
    ,variables
    ,inport_metadata
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests( doctest.DocTestSuite(source))
    tests.addTests(doctest.DocTestSuite(parameters))
    tests.addTests(doctest.DocTestSuite(variables))
    tests.addTests(doctest.DocTestSuite(inport_metadata))
    return tests
