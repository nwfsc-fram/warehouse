"""
Module defining a functional test suite for FRAM Data Warehouse management API

Copyright (C) 2017 ERT Inc.
"""
from unittest import TestCase
import codecs

import requests

import test_everything

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

get_base_URI = test_everything.get_base_URI

class WarehouseManagementApiV1(test_everything.WarehouseTestCaseBase):
    """
    unittest TestCase exercising the Data Warehouse v1 RESTful management API

    'requests' HTTP library used for API call/response. For usage info,
    see: http://docs.python-requests.org/
    """

    def test_dump(self):
        """
        validate /management_api/v1/dump/{type} is correct
        """
        for test_uri in [ '/management_api/v1/dump', '/management_api/v1/dump/']:
            url = ''.join([get_base_URI(), test_uri])
            with self.subTest(url=url):
                # check for redirect
                result = requests.get(url, allow_redirects=False, verify=False)
                self.assertEqual(result.status_code, 303, "HTTP GET redirects")
                expected_header_name, msg = 'location', "Header is set"
                self.assertIn(expected_header_name, [name.lower() #HTTP headers are case insensitive
                                                     for name    #per rfc7230 section 3.2
                                                     in result.headers], msg)
                self.assertEqual( result.headers[expected_header_name][-25:]
                                 ,'management_api/v1/dump/py'
                                 ,"Redirect value ends in Python dump URI")
                # expect no session!
                self.assertEqual(list(result.cookies), [], "No session cookie")
                # check header
                self.util_check_p3p_header(result)

        url = ''.join([get_base_URI(),'/management_api/v1/dump/py'])
        with self.subTest(url=url):
            # check that GET fails
            result = requests.get(url, verify=False)
            self.assertEqual(result.status_code, 401, "HTTP GET returns error")
            # expect a session
            expected_cookie_name = 'api.session.id'
            msg = "Anonymous session cookie"
            self.assertIn(expected_cookie_name, [c.name for c in result.cookies], msg)
            # check header
            self.util_check_p3p_header(result)
            # TODO: Test a Working login?
            # check header
            self.util_check_p3p_header(result)

    def test_p3p(self):
        """
        validate /management_api/v1/p3p.xml is correct

        Per API requirement: SERVER_20
        """
        url = ''.join([get_base_URI(),'/management_api/v1/p3p.xml'])
        with self.subTest(url=url):
            result = requests.get(url, verify=False)
            # check for error
            self.assertEqual(result.status_code, 200)
            # check format
            expected_content_type = 'text/xml'
            self.assertIn('content-type', result.headers)
            self.assertEqual(result.headers['content-type'], expected_content_type)
            # check contents
            expected_start_bytes = b'<?xml version="1.0" ?>'
            test = result.content.startswith(expected_start_bytes)
            msg = 'bytes ({}) must start the response from {}: ({})'.format(
                expected_start_bytes, url, result.content)
            self.assertTrue(test, msg)
            expected_end_bytes = b'</META>\n'
            test = result.content.endswith(expected_end_bytes)
            msg = 'bytes ({}) must end the response from {}: ({})'.format(
                expected_end_bytes, url, result.content)
            self.assertTrue(test, msg)
            # check header
            self.util_check_p3p_header(result)

    def test_help(self):
        """
        validate /management_api/v1/help is correct
        """
        url = ''.join([get_base_URI(),'/management_api/v1/help'])
        with self.subTest(url=url):
            # check response
            result = requests.get(url, verify=False)
            self.assertEqual(result.status_code, 200, "HTTP GET returns Okay")
            # check header
            expected_header = 'Content-Type'
            self.assertIn(expected_header, result.headers)
            expected_content_type = 'text/html; charset=utf-8'
            self.assertEqual(result.headers[expected_header], expected_content_type)
            expected_encoding = 'utf-8'
            self.assertEqual(result.encoding, expected_encoding)
            # check content
            self.assertIsInstance(result.content, bytes)
            response_text, decoded_length = codecs.utf_8_decode(result.content)
            expected_value = 'Management API'
            self.assertIn(expected_value, response_text)
            # check Privacy header
            self.util_check_p3p_header(result)
