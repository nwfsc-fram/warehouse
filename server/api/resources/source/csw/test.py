"""
Module providing unittest test discovery hook, for our Doctest testcases

Copyright (C) 2016 ERT Inc.
"""
import unittest
import doctest
import shutil

from api.resources.source.csw import (
    iso_metadata
    ,csw
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def csw_stop_thread():
    """
    unittest helper function, to stop csw module's background loop
    """
    csw.stop_update_thread()
    unit_test_temp_folder = csw.CswResponder(
        {}
        ,'warehouse-unittest1'
    )._get_api_temp_path()
    shutil.rmtree(unit_test_temp_folder)

def load_tests(loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(iso_metadata))
    csw_doctests = doctest.DocTestSuite(csw)
    for csw_doctest in csw_doctests:
        csw_doctest.addCleanup(csw_stop_thread)
    tests.addTests(csw_doctests)
    return tests
