"""
Authentication testcases

Copyright (C) 2016-2018 ERT Inc.
"""
__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>"

import doctest

from api.auth import (
     auth
    ,external
    ,ldap
)

def load_tests(loader, tests, ignore):
    """
    integrate Doctests with unittest test descovery API

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(auth))
    tests.addTests(doctest.DocTestSuite(external))
    tests.addTests(doctest.DocTestSuite(ldap))
    return tests
