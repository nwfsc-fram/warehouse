"""
Module providing unittest test discovery hook, for our Doctest testcases

Copyright (C) 2016 ERT Inc.
"""
import unittest
import doctest

from api.resources.source.warehouse import warehouse, sqlgenerator, util

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests( doctest.DocTestSuite( warehouse))
    tests.addTests( doctest.DocTestSuite( sqlgenerator))
    tests.addTests( doctest.DocTestSuite( util))
    return tests
