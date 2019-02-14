"""
Simple Python module, providing unittest discovery hook for doctest testcases

Copyright (C) 2017 ERT Inc.
"""
import unittest
import doctest

from . import (
     metadata
     ,service_provider
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(metadata))
    tests.addTests(doctest.DocTestSuite(service_provider))
    return tests
