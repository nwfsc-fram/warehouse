"""
Module providing unittest test discovery hook for our Doctest testcases

Copyright (C) 2016 ERT Inc.
"""
import unittest
import doctest

from api.handlers import middleware

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unitest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(middleware))
    return tests
