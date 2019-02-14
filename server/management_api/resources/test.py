"""
Module providing unittest test discovery hook, for our management endpoints

Copyright (C) 2017 ERT Inc.
"""
import unittest
import doctest

from . import (
     auth
    ,dump
    ,table
    ,usage_info
    ,variables
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(auth))
    tests.addTests(doctest.DocTestSuite(dump))
    tests.addTests(doctest.DocTestSuite(table))
    tests.addTests(doctest.DocTestSuite(usage_info))
    tests.addTests(doctest.DocTestSuite(variables))
    return tests
