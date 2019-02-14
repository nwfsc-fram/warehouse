"""
Simple Python module, providing unittest discovery hook for doctest testcases

Copyright (C) 2018 ERT Inc.
"""
import unittest
import doctest

from . import (
    login
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(login))
    return tests
