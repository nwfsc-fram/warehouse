"""
Module providing unittest test discovery hook, for our Doctest testcases

Copyright (C) 2016 ERT Inc.
"""
import unittest
import doctest

from . import (
    model
    ,prefetch_cache
)

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def prefetch_stop_thread():
    """
    unittest helper function, to stop prefetch_cache module's background loop
    """
    prefetch_cache.stop_update_thread()

def load_tests( loader, tests, ignore):
    """
    Expose Doctest testcases to unittest discovery

    per: https://docs.python.org/3/library/doctest.html#unittest-api
    """
    tests.addTests(doctest.DocTestSuite(model))
    prefetch_cache_tests = doctest.DocTestSuite(prefetch_cache)
    for prefetch_cache_doctest in prefetch_cache_tests:
        prefetch_cache_doctest.addCleanup(prefetch_stop_thread)
    tests.addTests(prefetch_cache_tests)
    return tests
