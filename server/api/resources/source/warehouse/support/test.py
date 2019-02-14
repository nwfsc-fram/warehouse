"""
Module providing unittest test discovery hook, for our Doctest testcases

Copyright (C) 2016 ERT Inc.
"""
import unittest
import doctest

from api.resources.source.warehouse.support import (
    configure
    ,discover
    ,dto_util
    ,model
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests( doctest.DocTestSuite( configure))
    tests.addTests( doctest.DocTestSuite( discover))
    tests.addTests( doctest.DocTestSuite( dto_util))
    return tests
