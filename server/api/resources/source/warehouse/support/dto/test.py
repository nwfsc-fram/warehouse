"""
Module providing unittest test discovery hook, for our Doctest testcases

Copyright (C) 2016-2017 ERT Inc.
"""
import unittest
import doctest

from api.resources.source.warehouse.support.dto import (
    table
    ,table_type
    ,project
    ,contact
    ,association
    ,association_type
    ,query
    ,variable
    ,variable_custom_identifier
    ,variable_python_type
    ,table_authorization
    ,management_authorization
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests( doctest.DocTestSuite( table))
    tests.addTests( doctest.DocTestSuite( table_type))
    tests.addTests( doctest.DocTestSuite( project))
    tests.addTests( doctest.DocTestSuite( contact))
    tests.addTests( doctest.DocTestSuite( association))
    tests.addTests( doctest.DocTestSuite( association_type))
    tests.addTests(doctest.DocTestSuite(query))
    tests.addTests( doctest.DocTestSuite( variable))
    tests.addTests(doctest.DocTestSuite(variable_custom_identifier))
    tests.addTests( doctest.DocTestSuite( variable_python_type))
    tests.addTests( doctest.DocTestSuite(table_authorization))
    tests.addTests( doctest.DocTestSuite(management_authorization))
    return tests
