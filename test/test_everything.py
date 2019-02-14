"""
Module defining a functional test suite for the FRAM Data Warehouse server

Copyright (C) 2015-2017 ERT Inc.
"""
from unittest import TestCase, skip
from copy import deepcopy
import os.path
import time
import logging
import configparser
import requests
import platform
from collections import namedtuple
from datetime import datetime
import pytz
import csv
import codecs
from math import ceil
from random import randint

import pyparsing
from lxml import etree
import pandas
import dateutil

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

str_suite_parameter_filename = 'test.ini'

dw200_selection_skip = ['warehouse'] #TODO: DW-200; re-enable check

class NoTestSettingsError(KeyError):
    """
    Exception, when 'test.ini' doesn't exist or has no heading:"[instance]"
    """

def _get_dict_suite_parameters():
    """
    retrieves suite test parameters from config file
    """
    # open & parse suite config file
    filename = str_suite_parameter_filename
    str_module_dir = os.path.dirname(__file__)
    str_path_to_config = os.path.join(str_module_dir, filename)
    config_parser = configparser.ConfigParser()
    config_parser.read( str_path_to_config)
    # return 'instance' heading, as dict
    try:
        section = config_parser['instance']
        return dict(section)
    except KeyError:
        str_msg = 'file test.ini DNE or is missing heading: [instance]'
        raise NoTestSettingsError(str_msg)

def get_base_URI():
    """
    Returns String representation of the base Warehouse URI to be tested
    """
    conf = _get_dict_suite_parameters()
    scheme, host, port = conf['scheme'], conf['host'], conf['port']
    # build URI, pointing to the API instance to be tested
    uri_protocol_plus_host = '{}://{}'.format(scheme, host)
    # immediately return with no port, if port specified is the default
    if (scheme.lower() == 'http'
            and port in ['80', '']):
        return uri_protocol_plus_host
    if (scheme.lower() == 'https'
            and port in ['443', '']):
        return uri_protocol_plus_host
    # append port to URI if a non-default port was specified
    uri_nondefault_port = uri_protocol_plus_host+':'+port
    return uri_nondefault_port

class WarehouseTestCaseBase(TestCase):
    """
    unittest TestCase providing test execution times & util functions
    """
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)

    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        self.logger.info("{}:seconds: {:.3f}".format(self.id(), t))

    def util_check_p3p_header(self, response):
        """
        utility function,for Test to confirm p3p header's present

        Per API requirement: SERVER_20
        """
        # check for header
        msg = "HTTP header 'P3P' must be present on *every* API response"
        self.assertIn('P3P', response.headers, msg)
        # check contents
        expected_value_prefix = 'policyref="'
        test = response.headers['P3P'].startswith(expected_value_prefix)
        msg =("""P3P header value starts with 'policyref="': {} (URL: {}"""
             ).format(response.headers['P3P'], response.url)

        expected_value_suffix = '/api/v1/p3p.xml"'
        test = response.headers['P3P'].endswith(expected_value_suffix)
        msg =("""P3P header value end with '/api/v1/p3p.xml"': {} (URL: {}"""
             ).format(response.headers['P3P'], response.url)
        self.assertTrue(test, msg)

class WarehousePythonPlatform(WarehouseTestCaseBase):
    """
    unittest TestCase validating the Python environment hosting these tests

    Assumption1: assume environment running functional tests was constructed
        the same way as the Anacondas environment running the Data Warehouse.
        (See: 'build' section of server/Makefile & compare with test/Makefile)
    """

    def test_version( self):
        """
        validate Python interpreter version
        """
        str_major, str_minor, str_patch_level = platform.python_version_tuple()
        str_msg_major = "Environment uses a Python 3 interpreter"
        self.assertEqual( str_major, "3", str_msg_major)
        self.assertEqual( str_minor, "6", "Interpreter version is 3.6")

class WarehouseEtlScheduler(WarehouseTestCaseBase):
    """
    unittest TestCase exercising the Data Warehouse ETL scheduler
    """
    test_expected_datasets_file = 'test_expected_jobs.csv'
    with open(test_expected_datasets_file) as expectations:
        expectation_dicts = [row for row in csv.DictReader(expectations)]
    expected_job_titles = [expectation['PENTAHO_JOB_TITLE'] for expectation in expectation_dicts]
    # collection of Pentaho job titles that are expected to be listed

    def test_status(self):
        """
        confirm Etl Scheduler subprocess has started & is running Jobs
        """
        conf = _get_dict_suite_parameters()
        scheme, host, port, username, pw = ('https', conf['host']
                                            , conf['etl.pentaho.port']
                                            , conf['etl.pentaho.username']
                                            , conf['etl.pentaho.password'])
        # test with a Cart URL for general status
        url = ('{}://{}:{}/kettle/status/?xml=y').format(scheme, host, port)
        with self.subTest(url=url):
            result = requests.get(url, auth=(username, pw), verify=False)
            # check for error
            self.assertEqual(result.status_code, 200)
            # check format
            expected_content_type = 'text/xml;charset=UTF-8'
            self.assertIn('content-type', result.headers)
            self.assertEqual(result.headers['content-type']
                             ,expected_content_type)
            # check contents
            response_xml = etree.XML(result.content) #should parse
            msg = 'XML should contain 1x <jobstatuslist> subelement'
            jobstatuslist_element = response_xml.find('jobstatuslist')
            self.assertIsNotNone(jobstatuslist_element, msg)
            # get status elements
            jobstatus_elements = jobstatuslist_element.getchildren()
            self.assertIsInstance(jobstatus_elements, list)
            self.assertEqual(len(jobstatus_elements), len(self.expected_job_titles)) #Check count
            for jobstatus_element in jobstatus_elements: #check status list
                with self.subTest(jobstatus_element=jobstatus_element):
                    # check name
                    msg_template = 'missing <{}> subelement'
                    jobname_child_element = jobstatus_element.find('jobname')
                    msg = msg_template.format('jobname')
                    self.assertIsNotNone(jobname_child_element, msg)
                    msg = ('Unrecognized Pentaho carte job found (not on'
                          ' test/test_expected_jobs.csv list!)')
                    self.assertIn(jobname_child_element.text, self.expected_job_titles, msg)
                    # check status
                    status_desc_child_element = jobstatus_element.find('status_desc')
                    msg = msg_template.format('status_desc')
                    self.assertIsNotNone(status_desc_child_element, msg)
                    expected_status = 'Running'
                    self.assertEqual(status_desc_child_element.text, expected_status)

class WarehouseApiV1(WarehouseTestCaseBase):
    """
    unittest TestCase exercising the Data Warehouse v1 RESTful API

    'requests' HTTP library used for API call/response. For usage info,
    see: http://docs.python-requests.org/
    """
    test_expected_datasets_file = 'test_expected_datasets.csv'
    with open(test_expected_datasets_file) as expectations:
        expectation_dicts = [row for row in csv.DictReader(expectations)]
    list_expected_sources = [expectation['API_ID'] for expectation in expectation_dicts]
    # collection of API data source id's that are expected to be listed

    dw440_selection_skip = [expectation['API_ID']
                            for expectation in expectation_dicts
                            if expectation['dw440_skip_selection_test'] is not '']
    # collection of API id's which are expected to be found, but not expected to be selectable
    sources_with_uuid = [expectation['API_ID']
                         for expectation in expectation_dicts
                         if expectation['no_csw_uuid'] in ('', None)
                           and expectation['API_ID'] != 'warehouse'#Warehouse does not have a CSW UUID
                        ]
    # collection of API id's which are expected to have CSW UUIDs


    #FIXME: some unfiltered dataset requests consume Huge ammount of memory in current implementation.
    str_filter_mock = 'trawl.MockRollupByDayHaulCharsSat$capture_date=2014-09-16T00:00:00Z'
    str_filter_dwcatch = 'taxonomy_dim$common_name=shark unident.,depth_dim$depth_meters=444.2'
    filter_trawl_individual = 'date_dim$year=2009,date_dim$month_of_year=10'
    #FIXME: some datasets are so big API server is being killed.
    #       Warehouse response must be streamed, or otherwise limit memory usage, such as by Filters below:
    dict_filters_by_source = {
         'warehouse':','.join([str_filter_mock,str_filter_dwcatch])
        ,'trawl.catch_fact': 'field_identified_taxonomy_dim$common_name=shark unident.'
        ,'hooknline.operation_hook_fact': 'date_dim$year=2014'
        ,'warehouse.longitude_dim': 'longitude_degree_units=0'
        ,'warehouse.latitude_dim': 'latitude_degree_units=0'
        ,'trawl.haul_longitude_dim': 'longitude_degree_units=0'
        ,'trawl.haul_latitude_dim': 'latitude_degree_units=0'
        ,'warehouse.drop_longitude_dim': 'longitude_degree_units=0'
        ,'warehouse.drop_latitude_dim': 'latitude_degree_units=0'
        ,'hooknline.ctd_drop_longitude_dim': 'longitude_degree_units=0'
        ,'hooknline.ctd_drop_latitude_dim': 'latitude_degree_units=0'
        ,'hooknline.individual_hooknline_view': 'common_name=ocean whitefish'
        ,'trawl.individual_fact': filter_trawl_individual
    }

    #FIXME: some unfiltered dataset requests consume Huge ammount of memory in current implementation.
    implicit_filter_mock = 'trawl.MockRollupByDayHaulCharsSat$capture_date=2014-09-16T00:00:00Z'
    implicit_filter_dwcatch = 'taxonomy_dim$common_name=shark unident.&depth_dim$depth_meters=444.2'
    implicit_filter_trawl_individual = 'date_dim$year=2009&date_dim$month_of_year=10'
    #FIXME: some datasets are so big API server is being killed.
    #       Warehouse response must be streamed, or otherwise limit memory usage, such as by Filters below:
    implicit_filter_and_variable_tuples_by_source = {
         'warehouse':'&'.join([implicit_filter_mock
                              ,implicit_filter_dwcatch
                              ])
        ,'trawl.catch_fact': ('field_identified_taxonomy_dim$common_name=shark unident.', 'field_identified_taxonomy_dim$common_name')
        ,'hooknline.operation_hook_fact': ('date_dim$year=2014', 'date_dim$year')
        ,'warehouse.longitude_dim': ('longitude_degree_units=0', 'longitude_degree_units')
        ,'warehouse.latitude_dim': ('latitude_degree_units=0', 'latitude_degree_units')
        ,'trawl.haul_longitude_dim': ('longitude_degree_units=0', 'longitude_degree_units')
        ,'trawl.haul_latitude_dim': ('latitude_degree_units=0', 'latitude_degree_units')
        ,'hooknline.drop_longitude_dim': ('longitude_degree_units=0', 'longitude_degree_units')
        ,'hooknline.drop_latitude_dim': ('latitude_degree_units=0', 'latitude_degree_units')
        ,'hooknline.ctd_drop_longitude_dim': ('longitude_degree_units=0', 'longitude_degree_units')
        ,'hooknline.ctd_drop_latitude_dim': ('latitude_degree_units=0', 'latitude_degree_units')
        ,'hooknline.individual_hooknline_view': ('common_name=ocean whitefish', 'common_name')
        ,'trawl.individual_fact': (implicit_filter_trawl_individual, 'date_dim$year')
    }

    def test_resource_source(self):
        """
        validate /api/v1/source is correct
        """
        url = ''.join([get_base_URI(),'/api/v1/source'])
        result = requests.get(url, verify=False)
        # check for error
        self.assertEqual( result.status_code, 200)
        # check header
        self.util_check_p3p_header(result)
        # check contents
        result_object = result.json() # should contain a json encoded object
        self.assertIsInstance( result_object, dict) # object should be dict
        self.assertIn('sources', result_object.keys())

        result_sources_list = result_object['sources']# sources key value ...
        self.assertIsInstance( result_sources_list, list) #... should be a list

        # check expected items
        list_expected_sources = self.list_expected_sources
        # duplicates in the expectations list
        duplicate_expectations = [api_id for api_id in list_expected_sources
                                  if list_expected_sources.count(api_id) > 1]
        msg = "No API_ID should be listed more than once in '{}'".format(self.test_expected_datasets_file)
        self.assertEqual(duplicate_expectations, [], msg)

        for result_source_obj in result_sources_list: # values of sources
            with self.subTest(result_source_obj=result_source_obj):
                self.assertIsInstance( result_source_obj, dict)
                # check properties
                expected_keys = {'id', 'name', 'defaults'
                                 ,'description', 'updated', 'rows'
                                 ,'is_selectable', 'selection_authorized'
                                 ,'is_sensitive', 'years'
                                 ,'project', 'contact', 'bounds', 'links', 'title'}
                msg = 'should exactly match expected attributes: {}'.format(
                    expected_keys)
                self.assertEqual(set(result_source_obj.keys()), expected_keys, msg)
                # check number of records
                str_msg = "bad "+result_source_obj['id']+" row count"
                self.assertIsInstance(result_source_obj['rows'], int, str_msg)

        # compare with TestCase's expectations
        result_api_ids = [source['id'] for source in result_sources_list]
        missing = [missing_source for missing_source in list_expected_sources
                   if missing_source not in result_api_ids]
        msg = "No '{}' API_IDs should be missing".format(self.test_expected_datasets_file)
        self.assertEqual(missing, [], msg)        
        extra = [extra_source for extra_source in result_api_ids
                   if extra_source not in list_expected_sources]
        msg = "No API_IDs not in '{}' should be listed".format(self.test_expected_datasets_file)
        self.assertEqual(extra, [], msg)
        # check for duplicates in the API response
        response_duplicates = [api_id for api_id in result_api_ids
                               if result_api_ids.count(api_id) > 1]
        msg = "No ID should be listed in source more than once"
        self.assertEqual(response_duplicates, [], msg)
        count_result = len(result_sources_list)
        count_expectation = len(list_expected_sources)
        self.assertEqual( count_result, count_expectation) #quantity of sources

        # HATEOS properties should be present
        self.assertIn('links', result_object.keys())
        result_links_list = result_object['links']# links key value ...
        self.assertIsInstance( result_links_list, list) #... should be a list
        self.assertEqual( len(result_links_list), 2, "Unexpected links count")
        first_obj_link_item, second_obj_link_item = result_links_list
        self.assertIsInstance(first_obj_link_item, dict, "1st links item isn't a dict")
        self.assertIn('rel', first_obj_link_item.keys(), "missing link property")
        self.assertIn('href', first_obj_link_item.keys(), "missing link property")
        self.assertEqual(first_obj_link_item['rel'], 'self', "unexpected relation")
        conf = _get_dict_suite_parameters()
        self.assertEqual(first_obj_link_item['href'], conf['proxy_url_base']+'/v1/source', "unexpected self link")
        self.assertIsInstance(second_obj_link_item, dict, "2nd links item isn't a dict")
        help_url = conf['proxy_url_base']+'/v1/help'
        self.assertIn('rel', second_obj_link_item.keys(), "missing link property")
        self.assertIn('href', second_obj_link_item.keys(), "missing link property")
        self.assertEqual(second_obj_link_item['rel'], 'help', "unexpected relation")
        self.assertEqual(second_obj_link_item['href'], help_url, "unexpected self link")
        # check other properties
        num_properties = len(result_object.keys())
        self.assertEqual( num_properties, 2, "Unexpected property count")

    def test_resource_source_ordering(self):
        """
        validate /api/v1/source sources are returned alphabetically

        Per API requirement: METADATA_01
        """
        url = ''.join([get_base_URI(),'/api/v1/source'])
        result = requests.get(url, verify=False)
        result_sources = result.json()['sources']

        # check if list of sources is already alphabetical
        expected_order = deepcopy(result_sources)
        expected_order.sort(key=lambda source: source['id'])
        msg = 'sources should be sorted alphabetically by ID'
        self.assertEqual(result_sources, expected_order, msg)

    def test_resource_login(self):
        """
        validate /api/v1/login operates
        """
        url = ''.join([get_base_URI(),'/api/v1/login'])
        # check that GET fails
        result = requests.get(url, verify=False)
        self.assertEqual(result.status_code, 405, "HTTP GET returns error")
        # expect no session!
        self.assertEqual(list(result.cookies), [], "No session cookies")
        # check header
        msg = "Failed GET indicates which HTTP method(s) is/are supported"
        self.assertIn('Allow', result.headers.keys(), msg)
        expected_method = 'POST'
        msg = "Login only supports HTTP POST"
        self.assertEqual(result.headers['Allow'], expected_method, msg)
        self.util_check_p3p_header(result)

        # check POST
        result = requests.post(url, data={}, verify=False)#Missing auth parameters
        self.assertEqual(result.status_code, 400)# Expect failure

        bad_login = {'username': 'brKDG!*5n.vanvaerenbergh'
                     ,'password': 'NoWayAboveUserExists'}
        result = requests.post(url, data=bad_login, verify=False)
        self.assertEqual(result.status_code, 401)
        # expect no session!
        self.assertEqual(list(result.cookies), [], "No session cookies")
        bad_login_text = result.text
        bad_password = {'username': 'brandon.vanvaerenbergh'
                       ,'password': 'NotMyPassword'}
        result = requests.post(url, data=bad_password, verify=False)
        self.assertEqual(result.status_code, 401)
        # expect no session!
        self.assertEqual(list(result.cookies), [], "No session cookies")
        msg = "Bad password error & bad Login error are identical"
        self.assertEqual(result.text, bad_login_text, msg)
        # TODO: Test a Working login?
        # check header
        self.util_check_p3p_header(result)

    def test_resource_logout(self):
        """
        validate /api/v1/logout operates
        """
        url = ''.join([get_base_URI(),'/api/v1/logout'])
        # check pubic/Anonymous response
        result = requests.get(url, verify=False)
        self.assertEqual(result.status_code, 200, "HTTP GET returns Okay")
        # expect a session (with an expiration time of right now)
        expected_header = "Set-Cookie"
        msg = "Sets an expiring session cookie"
        self.assertIn(expected_header, result.headers)
        set_cookie_header_value = result.headers[expected_header]
        expected_cookie_start = 'api.session.id='
        msg = "Sets an API session cookie"
        self.assertEqual(set_cookie_header_value[:len(expected_cookie_start)]
                         ,expected_cookie_start, msg)
        expected_cookie_contains = '; expires=' #an expires heading
        msg = "Sets an expiring cookie"
        self.assertIn(expected_cookie_contains, set_cookie_header_value, msg)
        expected_cookie_end = 'GMT; Path=/' #last part of expire time+context
        msg = "Set cookie has a path context"
        self.assertEqual(set_cookie_header_value[-1*len(expected_cookie_end):]
                         ,expected_cookie_end, msg)
        # check that cookie has expired
        cookie_id, cookie_expires, cookie_context = set_cookie_header_value.split(';')
        cookie_expires_time_string = cookie_expires.split('expires=').pop()
        cookie_expires_time = dateutil.parser.parse(cookie_expires_time_string)
        current_time = pytz.utc.localize(datetime.utcnow())
        self.assertTrue(cookie_expires_time <= current_time)
        # check contents
        result_object = result.json() # should contain a json encoded object
        self.assertIsInstance( result_object, dict) # object should be dict
        expected_attributes = {'title', 'description'}#item should have two properties
        self.assertEqual(set(result_object.keys()), expected_attributes)
        # check item properties
        expected_title = "Session closed"
        self.assertEqual(result_object['title'], expected_title)
        expected_description = "Done. No login session found"
        self.assertEqual(result_object['description'], expected_description)
        # check Privacy header
        self.util_check_p3p_header(result)

    def test_resource_user(self):
        """
        validate /api/v1/user operates
        """
        url = ''.join([get_base_URI(),'/api/v1/user'])
        # check pubic/Anonymous response
        result = requests.get(url, verify=False)
        self.assertEqual(result.status_code, 200, "HTTP GET returns Okay")
        # expect a session
        expected_cookie_name = 'api.session.id'
        msg = "Anonymous session cookie"
        self.assertIn(expected_cookie_name, [c.name for c in result.cookies], msg)
        # check contents
        result_object = result.json() # should contain a json encoded object
        self.assertIsInstance( result_object, dict) # object should be dict
        expected_object_attributes = ['user'] #object should have a single item
        self.assertEqual(list(result_object.keys()), expected_object_attributes)
        user_object = result_object['user'] #item should have two properties
        expected_user_attributes = {'id', 'description'}
        self.assertEqual(set(user_object.keys()), expected_user_attributes)
        # check item properties
        expected_user_description = "Anonymous user."
        self.assertEqual(user_object['description'], expected_user_description)
        expected_user_id = None
        self.assertEqual(user_object['id'], expected_user_id)
        # check Privacy header
        self.util_check_p3p_header(result)

    def test_external_login(self):
        """
        validate /api/v1/external/login operates
        """
        url = ''.join([get_base_URI(),'/api/v1/external/login'])
        # check that GET fails
        result = requests.get(url, verify=False)
        self.assertEqual(result.status_code, 405, "HTTP GET returns error")
        # expect no session!
        self.assertEqual(list(result.cookies), [], "No session cookies")
        # check header
        msg = "Failed GET indicates which HTTP method(s) is/are supported"
        self.assertIn('Allow', result.headers.keys(), msg)
        expected_method = 'POST'
        msg = "Login only supports HTTP POST"
        self.assertEqual(result.headers['Allow'], expected_method, msg)
        self.util_check_p3p_header(result)

        # check POST
        result = requests.post(url, data={}, verify=False)#Missing auth parameters
        self.assertEqual(result.status_code, 400)# Expect failure

        bad_login = {'username': 'brKDG!*5n.vanvaerenbergh@fake.nosuchtld'
                     ,'password': 'NoWayAboveUserExists'}
        result = requests.post(url, data=bad_login, verify=False)
        self.assertEqual(result.status_code, 401)
        # expect no session!
        self.assertEqual(list(result.cookies), [], "No session cookies")
        bad_login_text = result.text
        bad_password = {'username': 'brandon.vanvaerenbergh@ertcorp.com'
                       ,'password': 'NotMyPassword'}
        result = requests.post(url, data=bad_password, verify=False)
        self.assertEqual(result.status_code, 401)
        # expect no session!
        self.assertEqual(list(result.cookies), [], "No session cookies")
        msg = "Bad password error & bad Login error are identical"
        self.assertEqual(result.text, bad_login_text, msg)
        # TODO: Test a Working login?
        # check header
        self.util_check_p3p_header(result)

    def test_saml_attribute_consumer_service(self):
        """
        validate /api/v1/saml/?acs operates
        """
        url = ''.join([get_base_URI(),'/api/v1/saml/?acs'])
        with self.subTest(url=url):
            # check that GET fails
            result = requests.get(url, verify=False)
            self.assertEqual(result.status_code, 400, "HTTP GET returns error")
            # GET only for Single Logout Service (sls)
            msg = "HTTP GET is only for sls"
            self.assertIn('\\\"sls\\\" parameter is invalid', result.text, msg)
            # expect no session!
            self.assertEqual(list(result.cookies), [], "No session cookies")
            self.util_check_p3p_header(result)

            # check POST
            result = requests.post(url, data={}, verify=False)#Missing auth parameters
            self.assertEqual(result.status_code, 500)# Expect failure

            bad_login = {'SAMLResponse': '''PHNhbWxwOlJlc3BvbnNlIHhtbG5zOnNhbWxwPSJ1cm46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA6
cHJvdG9jb2wiIElEPSJzMmQ3NTlkMzAyZjU1NmE1ZDYwMTA1YzM3NDU4ZWRhYmIyOTU5NmVmZDAi
IFZlcnNpb249IjIuMCIgSXNzdWVJbnN0YW50PSIyMDE3LTEwLTExVDIzOjI3OjI1WiIgRGVzdGlu
YXRpb249Imh0dHBzOi8vbndjZGV2ZnJhbS5ud2ZzYy5ub2FhLmdvdi9hcGkvdjEvc2FtbC8/YWNz
Ij48c2FtbDpJc3N1ZXIgeG1sbnM6c2FtbD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmFz
c2VydGlvbiI+bm9hYS1vbmxpbmUtaWRwPC9zYW1sOklzc3Vlcj48c2FtbHA6U3RhdHVzIHhtbG5z
OnNhbWxwPSJ1cm46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA6cHJvdG9jb2wiPgo8c2FtbHA6U3Rh
dHVzQ29kZSB4bWxuczpzYW1scD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOnByb3RvY29s
IiBWYWx1ZT0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOnN0YXR1czpTdWNjZXNzIj4KPC9z
YW1scDpTdGF0dXNDb2RlPgo8L3NhbWxwOlN0YXR1cz48c2FtbDpBc3NlcnRpb24geG1sbnM6c2Ft
bD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmFzc2VydGlvbiIgSUQ9InMyYzBkZjJmYzU1
OGY0NzNmZGRmODdjNTMwNjY3OTBiMGVjNTM2NDQ0NSIgSXNzdWVJbnN0YW50PSIyMDE3LTEwLTEx
VDIzOjI3OjI1WiIgVmVyc2lvbj0iMi4wIj4KPHNhbWw6SXNzdWVyPm5vYWEtb25saW5lLWlkcDwv
c2FtbDpJc3N1ZXI+PGRzOlNpZ25hdHVyZSB4bWxuczpkcz0iaHR0cDovL3d3dy53My5vcmcvMjAw
MC8wOS94bWxkc2lnIyI+CjxkczpTaWduZWRJbmZvPgo8ZHM6Q2Fub25pY2FsaXphdGlvbk1ldGhv
ZCBBbGdvcml0aG09Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvMTAveG1sLWV4Yy1jMTRuIyIvPgo8
ZHM6U2lnbmF0dXJlTWV0aG9kIEFsZ29yaXRobT0iaHR0cDovL3d3dy53My5vcmcvMjAwMC8wOS94
bWxkc2lnI3JzYS1zaGExIi8+CjxkczpSZWZlcmVuY2UgVVJJPSIjczJjMGRmMmZjNTU4ZjQ3M2Zk
ZGY4N2M1MzA2Njc5MGIwZWM1MzY0NDQ1Ij4KPGRzOlRyYW5zZm9ybXM+CjxkczpUcmFuc2Zvcm0g
QWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwLzA5L3htbGRzaWcjZW52ZWxvcGVkLXNp
Z25hdHVyZSIvPgo8ZHM6VHJhbnNmb3JtIEFsZ29yaXRobT0iaHR0cDovL3d3dy53My5vcmcvMjAw
MS8xMC94bWwtZXhjLWMxNG4jIi8+CjwvZHM6VHJhbnNmb3Jtcz4KPGRzOkRpZ2VzdE1ldGhvZCBB
bGdvcml0aG09Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvMDkveG1sZHNpZyNzaGExIi8+CjxkczpE
aWdlc3RWYWx1ZT4yMFJ0NXMrZFROMVlKTVJTSnNtR0ZYd1d1a009PC9kczpEaWdlc3RWYWx1ZT4K
PC9kczpSZWZlcmVuY2U+CjwvZHM6U2lnbmVkSW5mbz4KPGRzOlNpZ25hdHVyZVZhbHVlPgpsTjdK
N25xc2VPT3ozWEJObXZYOE05ZCtKOTEvUGw2a09obmxCdzcva3BMTTBpNWdwajFLUmpER2hTb3Mv
NUdrSXFlRGJBMW90YU5JCnF2SXZnZmV3cjRZQWxYbEtOallKbGhDQ2FnWnpZRnh2MTY4NzFWbWsz
REVNbTQwZVp3WHo0QTdNT2p1MEFMS3Qra3hoZXJuZHY3VGoKUGd3U2dsc1l0MzlSQ0taU1U3bzZF
bndsaVd4NUg1L1gzN1k0MEhXUnpXMm5tQjVQcUJnU2trZ0VDV0c4aGpmNHZBRTNEMHYxbkJpNQph
VDFnaGlGN3B6RzZYSWIwMWprRjVWQ1pMQTloalk5VmprSHA2cFpVK01Kdm9QMEdxK3JpcmZRUllX
TGViMFlsTnBVMFQ0OXd6RFVhCitxNFQwaURQLzNOV0F0eTdRR09YSzF5Tk5qbHJJdHphMTZJd013
PT0KPC9kczpTaWduYXR1cmVWYWx1ZT4KPGRzOktleUluZm8+CjxkczpYNTA5RGF0YT4KPGRzOlg1
MDlDZXJ0aWZpY2F0ZT4KTUlJRXJ6Q0NBNWVnQXdJQkFnSURBSmxtTUEwR0NTcUdTSWIzRFFFQkN3
VUFNRjB4Q3pBSkJnTlZCQVlUQWxWVE1SZ3dGZ1lEVlFRSwpFdzlWTGxNdUlFZHZkbVZ5Ym0xbGJu
UXhEREFLQmdOVkJBc1RBMFJ2UkRFTU1Bb0dBMVVFQ3hNRFVFdEpNUmd3RmdZRFZRUURFdzlFClQw
UWdTVVFnVTFjZ1EwRXRNemd3SGhjTk1UWXdPVEV5TWpFd056TTFXaGNOTVRrd09URXpNakV3TnpN
MVdqQnlNUXN3Q1FZRFZRUUcKRXdKVlV6RVlNQllHQTFVRUNoTVBWUzVUTGlCSGIzWmxjbTV0Wlc1
ME1Rd3dDZ1lEVlFRTEV3TkViMFF4RERBS0JnTlZCQXNUQTFCTApTVEVOTUFzR0ExVUVDeE1FUkVs
VFFURWVNQndHQTFVRUF4TVZjM052TFdSbGRqSXVZM053TG01dllXRXVaMjkyTUlJQklqQU5CZ2tx
CmhraUc5dzBCQVFFRkFBT0NBUThBTUlJQkNnS0NBUUVBeXpNZnRrUVJvalpHSnVDY2txVTRzMkpH
ZUN5alZRbUdDWVRsait3QWoxa3kKOTh4SGRZdVMrcThRQ1Z0T1p3UVpJbWNtSFA4MkFYcjlqNEMz
dkxvUXhLNTkxOTYvSzZWY09LMCtWaHNQbUNIRjdJK3pIcTBjUkt3Rwp3aVdsTWJDMkVXVHY3T2VB
NGtSMFpUZDZSOU5EMEs2ekRIL0k1ZEdhMEZVSWR0QTRKQ25yYjNLaXF1dUlxVlpheDlvTGdtRWVR
NmcwCnJIUGs4ZXhkTmVFMVIyNXI2UXU2Tzc5VGRGOXBTL2k0RVUydXUwSVJSZFpxOEZmc01iWWkv
STYvSE1kMUt0QXpxeUR1V3BxMWZFN04KT2FjTXVZZmJMdjB4ZzVpSC80Z1Z6cFo2TTZ6ME1KcWtG
UXIzWGZFKytaeFB4Z2Fpc3BxSUhNK2pOcFNpU0l0VzUyNFU3UUlEQVFBQgpvNElCWVRDQ0FWMHdI
d1lEVlIwakJCZ3dGb0FVanNXNXpQek9qbE8wS3M3b0VTclBteWxzWjhvd0hRWURWUjBPQkJZRUZN
RzhNd25TCndRNWY0bVVBTGRDSndxRlVMQmZ0TUdjR0NDc0dBUVVGQndFQkJGc3dXVEExQmdnckJn
RUZCUWN3QW9ZcGFIUjBjRG92TDJOeWJDNWsKYVhOaExtMXBiQzl6YVdkdUwwUlBSRWxFVTFkRFFW
OHpPQzVqWlhJd0lBWUlLd1lCQlFVSE1BR0dGR2gwZEhBNkx5OXZZM053TG1ScApjMkV1Yldsc01B
NEdBMVVkRHdFQi93UUVBd0lGb0RBNUJnTlZIUjhFTWpBd01DNmdMS0FxaGlob2RIUndPaTh2WTNK
c0xtUnBjMkV1CmJXbHNMMk55YkM5RVQwUkpSRk5YUTBGZk16Z3VZM0pzTUNZR0ExVWRFUVFmTUIy
Q0ZYTnpieTFrWlhZeUxtTnpjQzV1YjJGaExtZHYKZG9jRWpGcDdUekFXQmdOVkhTQUVEekFOTUFz
R0NXQ0dTQUZsQWdFTEp6QW5CZ05WSFNVRUlEQWVCZ2dyQmdFRkJRY0RBUVlJS3dZQgpCUVVIQXdJ
R0NDc0dBUVVGQ0FJQ01BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRQkNHd01ONUR2Ty9jQWl0NDhF
VTVZUDgxVC9SRElFCityazR5RkpHd2NQR3JlamJGcGZYVWh0Umw2SVdla3RHTk4reksrdjV6cm9s
b1FiZlEvVzYyM2ZzYllEeVZ0QmpYMFdUdSt5OXY1Nm8KZkVYRmxZdSt6dmZDdG16b2labWJmQjQ3
SXo4OWNVS28rNTFPQjhWR0tvOWVyZm1jcGhTalNVZ3RJaGc3TTVKclZyUlFaQTM3VzBYbgo3T01n
c0VuS3ZsL3lpY1VQZ213WlJZbnNMc3ZRU2NkT3BRMDVmcW5BWStBUUlvbWxJeDBKOWpzbzZwWFlC
UG1hS3hIZmhCVDhJNGhPClBwTmR0Z1VsaFpKeTlRcVJ4b09VRHBIMjQ3L0RKM3hUaDJYcTRVS2pW
UXFTSWZxdDdlNVVJek5ZSTZlQmlpL1pTTCtpdlRjZGx5YzIKeEFObTFmNUkKPC9kczpYNTA5Q2Vy
dGlmaWNhdGU+CjwvZHM6WDUwOURhdGE+CjwvZHM6S2V5SW5mbz4KPC9kczpTaWduYXR1cmU+PHNh
bWw6U3ViamVjdD4KPHNhbWw6TmFtZUlEIEZvcm1hdD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6
MS4xOm5hbWVpZC1mb3JtYXQ6dW5zcGVjaWZpZWQiIE5hbWVRdWFsaWZpZXI9Im5vYWEtb25saW5l
LWlkcCIgU1BOYW1lUXVhbGlmaWVyPSJodHRwczovL253Y2RldmZyYW0ubndmc2Mubm9hYS5nb3Yv
YXBpL3YxL3NhbWwvbWV0YWRhdGEvIj5CcmFuZG9uLlZhblZhZXJlbmJlcmdoQG5vYWEuZ292PC9z
YW1sOk5hbWVJRD48c2FtbDpTdWJqZWN0Q29uZmlybWF0aW9uIE1ldGhvZD0idXJuOm9hc2lzOm5h
bWVzOnRjOlNBTUw6Mi4wOmNtOmJlYXJlciI+CjxzYW1sOlN1YmplY3RDb25maXJtYXRpb25EYXRh
IE5vdE9uT3JBZnRlcj0iMjAxNy0xMC0xMVQyMzozNzoyNVoiIFJlY2lwaWVudD0iaHR0cHM6Ly9u
d2NkZXZmcmFtLm53ZnNjLm5vYWEuZ292L2FwaS92MS9zYW1sLz9hY3MiLz48L3NhbWw6U3ViamVj
dENvbmZpcm1hdGlvbj4KPC9zYW1sOlN1YmplY3Q+PHNhbWw6Q29uZGl0aW9ucyBOb3RCZWZvcmU9
IjIwMTctMTAtMTFUMjM6MTc6MjVaIiBOb3RPbk9yQWZ0ZXI9IjIwMTctMTAtMTFUMjM6Mzc6MjVa
Ij4KPHNhbWw6QXVkaWVuY2VSZXN0cmljdGlvbj4KPHNhbWw6QXVkaWVuY2U+aHR0cHM6Ly9ud2Nk
ZXZmcmFtLm53ZnNjLm5vYWEuZ292L2FwaS92MS9zYW1sL21ldGFkYXRhLzwvc2FtbDpBdWRpZW5j
ZT4KPC9zYW1sOkF1ZGllbmNlUmVzdHJpY3Rpb24+Cjwvc2FtbDpDb25kaXRpb25zPgo8c2FtbDpB
dXRoblN0YXRlbWVudCBBdXRobkluc3RhbnQ9IjIwMTctMTAtMTFUMjM6MjM6NThaIiBTZXNzaW9u
SW5kZXg9InMyM2FjODNkYmJjOWFhOGY4NDA5ODFhODQyOTU0OThiNjc4NGRkYmYwMSI+PHNhbWw6
QXV0aG5Db250ZXh0PjxzYW1sOkF1dGhuQ29udGV4dENsYXNzUmVmPnVybjpvYXNpczpuYW1lczp0
YzpTQU1MOjIuMDphYzpjbGFzc2VzOnVuc3BlY2lmaWVkPC9zYW1sOkF1dGhuQ29udGV4dENsYXNz
UmVmPjwvc2FtbDpBdXRobkNvbnRleHQ+PC9zYW1sOkF1dGhuU3RhdGVtZW50PjxzYW1sOkF0dHJp
YnV0ZVN0YXRlbWVudD48c2FtbDpBdHRyaWJ1dGUgTmFtZT0ibWFpbCI+PHNhbWw6QXR0cmlidXRl
VmFsdWUgeG1sbnM6eHM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hIiB4bWxuczp4
c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiB4c2k6dHlwZT0i
eHM6c3RyaW5nIj5CcmFuZG9uLlZhblZhZXJlbmJlcmdoQG5vYWEuZ292PC9zYW1sOkF0dHJpYnV0
ZVZhbHVlPjwvc2FtbDpBdHRyaWJ1dGU+PHNhbWw6QXR0cmlidXRlIE5hbWU9InVpZCI+PHNhbWw6
QXR0cmlidXRlVmFsdWUgeG1sbnM6eHM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1h
IiB4bWxuczp4c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiB4
c2k6dHlwZT0ieHM6c3RyaW5nIj5CcmFuZG9uLlZhblZhZXJlbmJlcmdoPC9zYW1sOkF0dHJpYnV0
ZVZhbHVlPjwvc2FtbDpBdHRyaWJ1dGU+PHNhbWw6QXR0cmlidXRlIE5hbWU9ImVkaXBpIj48c2Ft
bDpBdHRyaWJ1dGVWYWx1ZSB4bWxuczp4cz0iaHR0cDovL3d3dy53My5vcmcvMjAwMS9YTUxTY2hl
bWEiIHhtbG5zOnhzaT0iaHR0cDovL3d3dy53My5vcmcvMjAwMS9YTUxTY2hlbWEtaW5zdGFuY2Ui
IHhzaTp0eXBlPSJ4czpzdHJpbmciPjE0MDU0MTAzMTg8L3NhbWw6QXR0cmlidXRlVmFsdWU+PC9z
YW1sOkF0dHJpYnV0ZT48L3NhbWw6QXR0cmlidXRlU3RhdGVtZW50Pjwvc2FtbDpBc3NlcnRpb24+
PC9zYW1scDpSZXNwb25zZT4='''}
            result = requests.post(url, data=bad_login, verify=False)
            self.assertEqual(result.status_code, 500)
            # expect no session!
            self.assertEqual(list(result.cookies), [], "No session cookies")
            # TODO: Test a Working login?

    def test_resource_help(self):
        """
        validate /api/v1/help operates
        """
        url = ''.join([get_base_URI(),'/api/v1/help'])
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
            expected_value = 'API Documentation'
            self.assertIn(expected_value, response_text)
            # check Privacy header
            self.util_check_p3p_header(result)

    def test_resource_p3p( self):
        """
        validate /api/v1/p3p.xml is correct

        Per API requirement: SERVER_20
        """
        url = ''.join([get_base_URI(),'/api/v1/p3p.xml'])
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

    def test_resource_inport_metadata(self):
        """
        validate /api/v1/source/{source_id}/metadata.xml is correct
        """
        source_id = 'warehouse'
        url = '{}/api/v1/source/{}/metadata.xml'.format(
                get_base_URI(), source_id)
        with self.subTest(url=url):
            result = requests.get(url, verify=False)
            # check for Expected error
            self.assertEqual(result.status_code, 400)
            # check header
            self.util_check_p3p_header(result)
        source_id = 'edc.catcher_vessel_cost_fact_conf'#TODO: check other sources
        url = '{}/api/v1/source/{}/metadata.xml'.format(
                get_base_URI(), source_id)
        with self.subTest(url=url):
            result = requests.get(url, verify=False)
            # check for error
            self.assertEqual(result.status_code, 200)
            # check header
            self.util_check_p3p_header(result)
            # check format
            expected_content_type = 'text/xml'
            self.assertIn('content-type', result.headers)
            self.assertEqual(result.headers['content-type'], expected_content_type)
            # check contents
            dtd_filename = 'inport_1_0_insert.dtd' #validate with our XML DTD
            with open(dtd_filename) as dtd_file:
                insert_dtd = etree.DTD(dtd_file)
            response_xml = etree.XML(result.content)
            test = insert_dtd.validate(response_xml)
            msg = ("Expected response to comply with test/{}.\n"
                   "  DTD errors: {}\n  failing URL: {}")
            errors = insert_dtd.error_log.filter_from_errors()
            self.assertTrue(test, msg.format(dtd_filename, errors, url))
            rng_filename = 'inport_1_0.rng' #validate with our RELAX NG schema
            with open(rng_filename) as rng_file:
                rng_xml = etree.parse(rng_file)
                relaxng = etree.RelaxNG(rng_xml)
            test = relaxng.validate(response_xml)
            msg = ("Expected response to comply with test/{}.\n"
                   "  RelaxNG errors: {}\n  failing URL: {}")
            errors = relaxng.error_log.filter_from_errors()
            self.assertTrue(test, msg.format(rng_filename, errors, url))

    def test_resource_csw_metadata(self):
        """
        validate /api/v1/source/{source_id}/metadata.iso is correct
        """
        source_id = 'warehouse'
        url = '{}/api/v1/source/{}/metadata.iso'.format(
                get_base_URI(), source_id)
        result = requests.get(url, verify=False)
        # check for Expected error
        self.assertEqual(result.status_code, 400)
        # check header
        self.util_check_p3p_header(result)
        source_id = self.list_expected_sources[1]#TODO: check other sources
        url = '{}/api/v1/source/{}/metadata.iso'.format(
                get_base_URI(), source_id)
        result = requests.get(url, verify=False)
        # check for error
        self.assertEqual(result.status_code, 200)
        # check header
        self.util_check_p3p_header(result)
        # check format
        expected_content_type = 'text/xml'
        self.assertIn('content-type', result.headers)
        self.assertEqual(result.headers['content-type'], expected_content_type)
        # check contents
        response_xml = etree.XML(result.content)
        gmd_xsd_url = 'http://schemas.opengis.net/iso/19139/20070417/gmd/gmd.xsd'#TODO: cache XSD locally, in case w3.org or others return HTTP errors while test is running.
        gmd_xsd = etree.XMLSchema(etree.parse(gmd_xsd_url))
        test = gmd_xsd.validate(response_xml)
        msg = ("Expected response to comply with {}.\n"
               "  XML Schema errors: {}\n  failing URL: {}")
        errors = gmd_xsd.error_log.filter_from_errors()
        self.assertTrue(test, msg.format(gmd_xsd_url, errors, url))

    def test_resource_csw(self):
        """
        validate /api/v1/csw is correct
        """
        # test with a CSW protocol request for '%' (i.e.: any) dataset
        url = ('{}/api/v1/csw?request=GetRecords&service=CSW'
               '&version=2.0.2&constraint=AnyText+like+%27%25%27'
               '&constraintLanguage=CQL_TEXT&constraint_language_version=1.1.0'
               '&typeNames=csw:Record&ElementSetName=full').format(get_base_URI())
        result = requests.get(url, verify=False)
        # check for error
        self.assertEqual(result.status_code, 200)
        # check header
        self.util_check_p3p_header(result)
        # check format
        expected_content_type = 'text/xml'
        self.assertIn('content-type', result.headers)
        self.assertEqual(result.headers['content-type'], expected_content_type)
        # check contents
        response_xml = etree.XML(result.content)
        csw_xsd_url = 'http://www.opengis.net/cat/csw/2.0.2'#TODO: cache XSD locally, in case opengis.net or others return HTTP errors while test is running.
        csw_xsd = etree.XMLSchema(etree.parse(csw_xsd_url))
        test = csw_xsd.validate(response_xml)
        msg = ("Expected response to comply with {}.\n"
               "  XML Schema errors: {}\n  failing URL: {}")
        errors = csw_xsd.error_log.filter_from_errors()
        self.assertTrue(test, msg.format(csw_xsd_url, errors, url))
        # check that 'search results' element is present
        expected_element_tag = '{http://www.opengis.net/cat/csw/2.0.2}SearchResults'
        self.assertIn(expected_element_tag, [e.tag for e in response_xml.getchildren()])
        for element in response_xml.getchildren():
            if element.tag == expected_element_tag:
                search_results_element = element
                expected_attribute = 'numberOfRecordsMatched'
                self.assertIn(expected_attribute, search_results_element.keys())
                # check that DWSupport inventory was ingested
                warehouse_source = 1 # one source has the special ID 'warehouse'
                # csw metadata cannot currently be generated for 'warehouse'
                # (regardless of whether an UUID has been specified for it)
                sources_without_uuid = 0 #check if any other sources lack a UUID
                if len(self.sources_with_uuid) < (len(self.list_expected_sources)
                                                   - warehouse_source):
                    #PyCSW will try saving all sources with UUID as id 'None'
                    # when metadata for these sources is processed
                    sources_without_uuid = 1 #account for this extra id 'None'
                expected_data_items = sources_without_uuid + len(self.sources_with_uuid)
                msg = ('<{}/> {} attribute value should match number of '
                       'distinct UUID "test/{}"'
                       ' entries ({})').format('csw:SearchResults'
                                               ,expected_attribute
                                               ,self.test_expected_datasets_file
                                               ,expected_data_items)
                if len(self.list_expected_sources) > len(self.sources_with_uuid):
                    msg = msg + (' + 1 (for all the sets without a CSW'
                                 ' identifier, collectively stored as ID:'
                                 ' "None")')
                csw_matched_records = search_results_element.get(
                    expected_attribute)
                expected_string = str(expected_data_items)
                self.assertEqual(csw_matched_records, expected_string, msg)

    def test_resource_variables( self):
        """
        validate /api/v1/source/{source_id}/variables is correct
        """
        response_sec_by_url = {}
        for source_id in self.list_expected_sources:
            if source_id in dw200_selection_skip+['site_dim', 'sex_dim', 'lab_maturity_detail_dim', 'hook_dim', 'disposition_dim', 'inclusion_dim', 'person_dim', 'angler_person_dim', 'drop_latitude_dim', 'drop_time_dim', 'drop_longitude_dim', 'drop_sounder_depth_dim', 'most_recent_age_update_date_dim']: #TODO: DW-200; re-enable check
                continue #TODO: DW-200; re-enable check
            if source_id in self.dw440_selection_skip: #TODO: DW-440, add fields to DWSupport
                continue
            url = '{}/api/v1/source/{}/variables'.format(
                get_base_URI(), source_id)
            result = requests.get(url, verify=False)
            # check for error
            self.assertEqual( result.status_code, 200, url)
            # check header
            self.util_check_p3p_header(result)
            # check contents
            result_object = result.json()
            self.assertIsInstance( result_object, dict, url)# object should be dict
            dict_result = result_object
            self.assertIn('links', dict_result.keys(), url)
            self.assertIn('variables', dict_result.keys(), url)
            object_variables = dict_result['variables']
            self.assertIsInstance( object_variables, list, url)# object should be list
            num_variables = len(object_variables)
            self.assertTrue( num_variables >=2,"dataset has 2+ variables: "+url)
            response_sec_by_url[url] = result.elapsed.total_seconds()
        # check response times
        row_name = 'secs'
        init_frame = pandas.DataFrame(data=response_sec_by_url, index=[row_name])
        two_columns = init_frame.transpose()#transpose frame to 2x col:url,secs
        descriptive_stats = two_columns.describe().transpose()
        ordered = two_columns.sort_values(by=row_name, ascending=False)[row_name]
        msg ="Expected lower mean response.\n  times: \n{}".format(ordered)
        self.assertLess(float(descriptive_stats['mean']), 1.741, msg)#loosening this, from 50ms
        msg ="Expected lower top percentile response.\n  times: \n{}".format(ordered)
        self.assertLess(float(descriptive_stats['75%']), 2.150, msg)
        msg ="Expected lower maximum response.\n  times: \n{}".format(ordered)
        self.assertLess(float(descriptive_stats['max']), 4.303, msg)

    def test_variables_role_description( self):
        """
        validate /api/v1/source/{source_id}/variables discriptions
        """
        cases = [ ( 'warehouse.time_dim', "hh24miss"
                   ,"HH24MISS")#check 1x dimension
                 ,( 'warehouse.sampling_end_time_dim', "sampling_end_hhmmss"
                   ,"Sampling End HH24MISS") #check 1x Role
                 ,( 'trawl.individual_fact', "sampling_end_hhmmss"
                   ,"Sampling End HH24MISS") #check 1x Fact
        ]
        for source_id, id_value, expected_value in cases:
            url = '{}/api/v1/source/{}/variables'.format(
                get_base_URI(), source_id)
            result = requests.get(url, verify=False)
            # check for error
            self.assertEqual( result.status_code, 200, url)
            # check header
            self.util_check_p3p_header(result)
            # check contents
            result_object = result.json()
            self.assertIsInstance( result_object, dict, url)# object should be dict
            dict_result = result_object
            self.assertIn('links', dict_result.keys(), url)
            self.assertIn('variables', dict_result.keys(), url)
            object_variables = dict_result['variables']
            self.assertIsInstance(object_variables, list, url)# object should be list
            for var in object_variables:
                if var['id'] == id_value:
                    msg = "Expected '"+id_value+"' variable description: "+url
                    self.assertEqual(var["title"], expected_value, msg)
                    break
            else:
                self.assertTrue(False,"Expected variable id 'hh24miss': "+url)

    def test_variables_custom_ids(self):
        """
        validate 'variables' endpoint uses available Custom variable IDs
        """
        TestCase = namedtuple('TestCase', [ "source_id"
                                           ,"default_field_id"
                                           ,"custom_field_id"])
        custom_fact_field_ids = [
            TestCase(
                 source_id="trawl.catch_fact"
                ,default_field_id="best_available_taxonomy_dim$scientific_name"
                ,custom_field_id="scientific_name"
            )
        ]
        for case in custom_fact_field_ids:
            url = '{}/api/v1/source/{}/variables'.format( get_base_URI()
                                                         ,case.source_id)
            with self.subTest(test_case=case, url=url):
                result = requests.get(url, verify=False)
                # check for error
                self.assertEqual(result.status_code, 200)
                # check header
                self.util_check_p3p_header(result)
                # check contents
                result_dict = result.json()
                self.assertIn('variables', result_dict.keys())
                object_variables = result_dict['variables']
                self.assertIsInstance(object_variables, list)# object should be list
                variable_ids = [v['id'] for v in object_variables]
                self.assertIn(case.custom_field_id, variable_ids)
                self.assertNotIn(case.default_field_id, variable_ids)

    def test_resource_variables_comparison(self):
        """
        validate /api/v1/source/{source_id}/variables against selection
        """
        sample_percent = 0.03 # each run, test only 3% of sources
        #TODO: consider refactoring below lines,into a reusable helper function
        test_count = ceil(len(self.list_expected_sources)*sample_percent)
        # min 1 source per test run, so many runs test all sources (eventually)
        test_sample_source_ids = set()
        while len(test_sample_source_ids) < test_count:
            # pick another random source
            random_index = randint(0,len(self.list_expected_sources)-1)
            random_source = self.list_expected_sources[random_index]
            test_sample_source_ids.add(random_source)
        # compare
        for source_id in test_sample_source_ids:
            with self.subTest(source_id=source_id):
                if source_id in dw200_selection_skip: #TODO: DW-200; re-enable check
                    continue #TODO: DW-200; re-enable check
                if source_id.endswith('_conf'): #TODO: DW-440; use API to determine selectability
                    continue#FIXME: for some reason, self.skipTest skips more than just 1x subTest?
                if source_id in self.dw440_selection_skip: #TODO: DW-440, add fields to DWSupport
                    continue#FIXME: for some reason, self.skipTest skips more than just 1x subTest?
                url = '{}/api/v1/source/{}/variables'.format(
                    get_base_URI(), source_id)
                result = requests.get(url, verify=False)
                # check for error
                self.assertEqual(result.status_code, 200, url)
                # check contents
                result_object = result.json()
                self.assertIsInstance(result_object, dict, url)# object should be dict
                dict_result = result_object
                self.assertIn('links', dict_result.keys(), url)
                self.assertIn('variables', dict_result.keys(), url)
                object_variables = dict_result['variables']
                self.assertIsInstance(object_variables, list, url)# object should be list
                # Record what variable names are present, for later comparision
                variable_names_shortened = []
                selection_filters = { #also check if certain DIM fields are present
                     'date_dim$year': False # These fields can be used to speed up select
                    ,'latitude_in_degrees': False
                    ,'longitude_in_degrees': False
                }
                for variable in object_variables:
                    api_id = variable['id']
                    max_pgsql_field_name_length = 63
                    variable_names_shortened.append(api_id[:max_pgsql_field_name_length])
                    if api_id in selection_filters:
                        selection_filters[api_id] = True
                # Check variables against selection
                # fetch multiple .CSV selections, to try & get all 'variables'
                def vars_to_multiple_variables_args(variable_names, limit=1900):
                    """
                    Return list of str,to make several 'variables=' URLs
                    
                    >>> names = ['ab','bc','cd','de','ef','f0']
                    >>> vars_to_multiple_variables_args(names, 5)
                    ['ab,bc', 'cd,de', 'ef,f0']
                    >>> vars_to_multiple_variables_args(names, 8)
                    ['ab,bc,cd', 'de,ef,f0']
                    """
                    variables_queries = ['']
                    for i,name in enumerate(variable_names):
                        if len(variables_queries[-1]) >= limit:
                            new_query = ''
                            variables_queries.append(new_query)
                        if len(variables_queries[-1]) > 0:
                            variables_queries[-1] = variables_queries[-1] + ','
                        variables_queries[-1] = variables_queries[-1] + name
                    return variables_queries
                variables_query_args = vars_to_multiple_variables_args(
                    variable_names_shortened)
                all_selection_urls = []
                all_selection_result_headers = []
                for variables_argument in variables_query_args:
                    #fetch a .CSV selection & see how many variables it has..
                    some_variables ='?variables='+variables_argument
                    selection_url = '{}/api/v1/source/{}/selection.csv'.format(
                        get_base_URI(), source_id)+some_variables
                    # filter datasets
                    filters = []
                    if selection_filters['date_dim$year']: #if possible, filter out ALL records
                        filters.append('date_dim$year=0')
                    if selection_filters['latitude_in_degrees']:
                        filters.append('latitude_in_degrees=91')
                    if selection_filters['longitude_in_degrees']:
                        filters.append('longitude_in_degrees=181')
                    #FIXME: some datasets are so big API server is being killed.
                    #       Warehouse response must be streamed, or otherwise limit memory usage, such as by Filters below:
                    if source_id in self.dict_filters_by_source.keys():
                        filters.append(self.dict_filters_by_source[source_id])
                    if filters:
                        selection_url = (selection_url+'&filters='+','.join(filters))
                    with self.subTest(selection_url=selection_url):
                        selection_result = requests.get(selection_url, verify=False)
                        msg = ("failed to select data, for comparison"
                               " against this source's 'variables' list")
                        self.assertEqual(selection_result.status_code, 200, msg)
                        # check contents
                        result_object = selection_result.content
                        msg = 'HTTP response is bytes'
                        self.assertIsInstance(result_object, bytes, msg)
                        #parse the response, as a CSV (Microsoft-style UTF8)
                        content_rows = codecs.decode(result_object, 'utf-8-sig').split('\r\n')
                        content_csv_rows = [row for row in csv.reader(content_rows)]
                        msg = "no dataset's less than {} rows (url: {})"
                        result_rows = len(content_csv_rows)
                        expected_rows = 1 + 1 #1x header, 1x HTTP newline
                        self.assertTrue(result_rows >=expected_rows
                                       ,msg.format(expected_rows,selection_url))
                        selection_headers = content_csv_rows[0]
                        #each selection column name, should have been in the variables list
                        msg = ("expected all 'selection_url' fields to also be"
                               " in 'url' variables")
                        for selection_field in selection_headers:
                            self.assertIn(selection_field, variable_names_shortened, msg)
                        all_selection_result_headers.extend(selection_headers)
                        all_selection_urls.append(selection_url)
                with self.subTest(selection_urls=all_selection_urls):
                    #.CSV selection should have same # of fields,as variables endpoint
                    msg = "expected matching # of 'selection_urls' fields, for comparison with 'url' variables"
                    self.assertEqual(set(variable_names_shortened), set(all_selection_result_headers), msg)
                    #each variables item should also be in the .CSV selection
                    msg = 'expected all variable items to be in .CSV selections'
                    for variable_id in variable_names_shortened:
                        self.assertIn(variable_id, all_selection_result_headers, msg)

    def test_resource_selection(self):
        """
        validate /api/v1/source/{source_id}/selection.{format} is correct
        """
        # check formats for a single data set
        source_id = 'trawl.operation_haul_fact'
        with self.subTest(source_id=source_id):
            # check json formatted output
            format_id = 'json'
            with self.subTest(format_id=format_id):
                if source_id in dw200_selection_skip: #TODO: DW-200; re-enable check
                    self.skipTest('dw200 skip') #TODO: DW-200; re-enable check
                if source_id.endswith('_conf'): #TODO: DW-440; use API to determine selectability
                    self.skipTest('_conf skip')
                if source_id in self.dw440_selection_skip: #TODO: DW-440, add fields to DWSupport
                    self.skipTest('dw440 skip')
                url = '{}/api/v1/source/{}/selection.{}'.format(
                    get_base_URI(), source_id,format_id)
                #FIXME: some datasets are so big API server is being killed.
                #       Warehouse response must be streamed, or otherwise limit memory usage, such as by Filters below:
                if source_id in self.dict_filters_by_source.keys():
                   url = url+'?filters='+self.dict_filters_by_source[ source_id]
                result = requests.get(url, verify=False)
                # check for error
                self.assertEqual(result.status_code, 200, url)
                # check header
                self.util_check_p3p_header(result)
                expected_header = "Transfer-encoding" # streamed response
                self.assertIn(expected_header, result.headers)
                expected_encoding = "chunked"
                self.assertEqual(result.headers[expected_header], expected_encoding)
                # check contents
                self.assertFalse(result.content.startswith(codecs.BOM_UTF8)
                                 ,'JSON should not be utf-8-sig encoded')
                result_object = result.json()
                self.assertIsInstance(result_object, list)
                result_rows = len(result_object)
                expected_rows = 6
                msg = "no dataset's less than {} rows (url: {})"
                self.assertTrue(result_rows >=expected_rows
                               ,msg.format(expected_rows,url))
            # check csv formatted output
            format_id = 'csv'
            with self.subTest(format_id=format_id):
                if source_id in dw200_selection_skip: #TODO: DW-200; re-enable check
                    self.skipTest('dw200 skip') #TODO: DW-200; re-enable check
                if source_id.endswith('_conf'): #TODO: DW-440; use API to determine selectability
                    self.skipTest('_conf skip')
                if source_id in self.dw440_selection_skip: #TODO: DW-440, add fields to DWSupport
                    self.skipTest('dw440 skip')
                url = '{}/api/v1/source/{}/selection.{}'.format(
                    get_base_URI(), source_id,format_id)
                #FIXME: some datasets are so big API server is being killed.
                #       Warehouse response must be streamed, or otherwise limit memory usage, such as by Filters below:
                if source_id in self.dict_filters_by_source.keys():
                   url = url+'?filters='+self.dict_filters_by_source[ source_id]
                result = requests.get(url, verify=False)
                # check for error
                self.assertEqual(result.status_code, 200, url)
                # check header
                self.util_check_p3p_header(result)
                # check contents
                result_object = result.content
                #check for Microsoft-compatible UTF8 encoding
                self.assertIsInstance(result_object, bytes)
                codecs.decode(result_object, 'utf-8-sig')
                #check CSV data
                result_rows = len(result_object.splitlines())
                expected_rows = 6
                msg = "no dataset's less than {} rows (url: {})"
                self.assertTrue(result_rows >=expected_rows
                               ,msg.format(expected_rows,url))
        # check a dimension, and a dimension role to ensure sql generator works
        additional_source_ids = ['warehouse.sex_dim'
                                 ,'warehouse.best_available_taxonomy_dim']
        for source_id in additional_source_ids:
            msg = 'check SQL generator output'
            with self.subTest(source_id=source_id, msg=msg):
                if source_id in dw200_selection_skip: #TODO: DW-200; re-enable check
                    self.skipTest('dw200 skip') #TODO: DW-200; re-enable check
                if source_id.endswith('_conf'): #TODO: DW-440; use API to determine selectability
                    self.skipTest('_conf skip')
                if source_id in self.dw440_selection_skip: #TODO: DW-440, add fields to DWSupport
                    self.skipTest('dw440 skip')
                # get 1x variable name
                url = '{}/api/v1/source/{}/variables'.format(
                        get_base_URI(), source_id)
                with self.subTest(url=url):
                    result = requests.get(url, verify=False)
                    # check for error
                    self.assertEqual(result.status_code, 200, url)
                    # get content variable name
                    result_variables = result.json()['variables']
                    variable = result_variables[0] #just pick 1st one
                    variable_name = variable['id']
                url = '{}/api/v1/source/{}/selection.{}?variables={}'.format(
                    get_base_URI(), source_id, format_id, variable_name)
                with self.subTest(url=url):
                    #FIXME: some datasets are so big API server is being killed.
                    #       Warehouse response must be streamed, or otherwise limit memory usage, such as by Filters below:
                    if source_id in self.dict_filters_by_source.keys():
                       url = url+'&filters='+self.dict_filters_by_source[ source_id]
                    result = requests.get(url, verify=False)
                    # check for error
                    self.assertEqual(result.status_code, 200)
                    # check header
                    self.util_check_p3p_header(result)
                    expected_header = "Transfer-encoding" # streamed response
                    self.assertIn(expected_header, result.headers)
                    expected_encoding = "chunked"
                    self.assertEqual(result.headers[expected_header], expected_encoding)
                    # check contents
                    result_object = result.content
                    #check for Microsoft-compatible UTF8 encoding
                    self.assertIsInstance(result_object, bytes)
                    codecs.decode(result_object, 'utf-8-sig')
                    #check CSV data
                    result_rows = len(result_object.splitlines())
                    expected_rows = 6
                    msg = "no dataset's less than {} rows"
                    self.assertTrue(result_rows >=expected_rows
                                   ,msg.format(expected_rows))

    def test_resource_selection_filters(self):
        """
        validate /api/v1/source/{source_id}/selection.{format}?filters={filters} behavior
        """
        # check formats for a single data set
        source_id = 'trawl.operation_haul_fact'
        with self.subTest(source_id=source_id):
            test_filters_and_expected_row_counts = [
              ('year=2003,depth_m<30', 3)
             ,('year=2003,depth_m<=26.4855', 2)
             ,('vessel~=Blue [H]orizo.*', 325)
            ]
            for test_filter,expected_rows in test_filters_and_expected_row_counts:
                with self.subTest(filter_value=test_filter):
                    # check json formatted output
                    url = '{}/api/v1/source/{}/selection.json?filters={}'.format(
                        get_base_URI(), source_id,test_filter)
                    result = requests.get(url, verify=False)
                    # check for error
                    self.assertEqual(result.status_code, 200, url)
                    # check header
                    self.util_check_p3p_header(result)
                    expected_header = "Transfer-encoding" # streamed response
                    self.assertIn(expected_header, result.headers)
                    expected_encoding = "chunked"
                    self.assertEqual(result.headers[expected_header], expected_encoding)
                    # check contents
                    result_object = result.json()
                    self.assertIsInstance(result_object, list)
                    result_rows = len(result_object)
                    msg = "selection's less than {} rows (url: {})"
                    self.assertTrue(result_rows >=expected_rows
                                   ,msg.format(expected_rows,url))

    def test_selection_custom_ids(self):
        """
        validate 'selection' endpoint uses available Custom variable IDs
        """
        TestCase = namedtuple('TestCase', [ "source_id"
                                           ,"default_field_id"
                                           ,"custom_field_id"])
        custom_fact_field_ids = [
            TestCase(
                 source_id="trawl.catch_fact"
                ,default_field_id="best_available_taxonomy_dim$scientific_name"
                ,custom_field_id="scientific_name"
            )
        ]
        for case in custom_fact_field_ids:
            url = '{}/api/v1/source/{}/selection.json?variables={}'.format(
                  get_base_URI()
                 ,case.source_id
                 ,case.default_field_id)
            if case.source_id in self.dict_filters_by_source.keys():
                filters = self.dict_filters_by_source[case.source_id]
                url = url+'&filters='+filters
            with self.subTest(test_case=case, url=url):
                http_result = requests.get(url, verify=False)
                # check for error
                self.assertEqual(http_result.status_code, 200)
                # check contents
                selection = http_result.json()
                self.assertIsInstance(selection, list)
                for row in selection:
                    with self.subTest(selection_row=row):
                        self.assertNotIn(case.default_field_id, row.keys())

    def test_selection_variables_custom_ids(self):
        """
        validate 'selection' variables parameter uses Custom variable ID
        """
        TestCase = namedtuple('TestCase', [ "source_id"
                                           ,"custom_field_id"])
        custom_fact_field_ids = [
            TestCase(
                 source_id="trawl.catch_fact"
                ,custom_field_id="scientific_name"
            )
        ]
        for case in custom_fact_field_ids:
            url = '{}/api/v1/source/{}/selection.json'.format( get_base_URI()
                                                              ,case.source_id)
            with self.subTest(test_case=case, url=url):
                url = url+'?variables='+case.custom_field_id
                if case.source_id in self.dict_filters_by_source.keys():
                    filters = self.dict_filters_by_source[case.source_id]
                    url = url+'&filters='+filters
                http_result = requests.get(url, verify=False)
                # check for error
                self.assertEqual(http_result.status_code, 200)
                # check contents
                selection = http_result.json()
                self.assertIsInstance(selection, list)
                for row in selection:
                    with self.subTest(selection_row=row):
                        expected_keys = set([case.custom_field_id])
                        self.assertEqual(set(row.keys()), expected_keys)

    def test_resource_selection_malformed_filters(self):
        """
        validate that malformed URL parameters are reported correctly to user

        per API requirement SELECTION_08
        """
        # check malformed filters
        source_id = 'warehouse.person_dim' # arbitrary source
        url = '{}/api/v1/source/{}/selection.{}'.format(
            get_base_URI(), source_id, 'json')
        url = url+'?filters=sdfosghsneblr<>90s0sf'
        result = requests.get(url, verify=False)
        # check status
        expected_status = 400
        self.assertEqual( result.status_code, expected_status, url)

    def test_resource_selection_implicit_filter(self):
        """
        validate /api/v1/source/{source_id}/selection.{format} filtering
        via implicit, specification of variable names as HTTP param, is correct
        """
        min_rows_expected = 5
        format_id = 'json'
        # check implicit filtering expressions
        for source_id in self.implicit_filter_and_variable_tuples_by_source.keys():
            with self.subTest(source_id=source_id):
                if source_id in dw200_selection_skip: #TODO: DW-200; re-enable check
                    self.skipTest('dw200 skip') #TODO: DW-200; re-enable check
                if source_id.endswith('_conf'): #TODO: DW-440; use API to determine selectability
                    self.skipTest('_conf skip')
                if source_id in self.dw440_selection_skip: #TODO: DW-440, add fields to DWSupport
                    self.skipTest('dw440 skip')
                url = '{}/api/v1/source/{}/selection.{}'.format(
                    get_base_URI(), source_id,format_id)
                #TODO: refactor the DW-241 workaround filters into a
                # dedicated parameters list for *this* functional test case
                implicit_filter, variable_name = self.implicit_filter_and_variable_tuples_by_source[source_id]
                url = url+'?'+ implicit_filter + '&variables={}'.format(variable_name)
                result = requests.get(url, verify=False)
                # check for error
                self.assertEqual(result.status_code, 200, url)
                # check header
                self.util_check_p3p_header(result)
                # check contents
                result_object = result.json()
                self.assertIsInstance(result_object, list)
                result_rows = len(result_object)
                msg = "no dataset's less than {} rows, (url: {})"
                msg = msg.format(min_rows_expected, url)
                self.assertTrue(result_rows >=min_rows_expected, msg)

    def test_resource_selection_variables( self):
        """
        validate selection REST endpoint parameter: variables={list,of,vars}
        """
        # check json formatted output
        format_id = 'json'
        source_id = 'trawl.operation_haul_fact'
        list_variables = ['seafloor_depth_dim$record_type','o2_at_gear_ml_per_l_der']
        variables = ','.join( list_variables) #make into comma-delimited string
        url = '{}/api/v1/source/{}/selection.{}?variables={}&date_yyyymmdd=20141010'.format(
            get_base_URI(), source_id,format_id,variables)
        result = requests.get(url, verify=False)
        # check for error
        self.assertEqual( result.status_code, 200)
        # check header
        self.util_check_p3p_header(result)
        # check contents
        result_object = result.json()
        self.assertIsInstance( result_object, list)
        result_rows = len(result_object)
        self.assertTrue( result_rows >=9,"selection's at least 9 rows")
        result_list_of_rows = result_object
        for obj_row in result_list_of_rows:
            msg = 'every row should encode a dict'
            self.assertIsInstance( obj_row, dict)
            dict_row = obj_row
            for variable in list_variables:
                msg = 'every row should have variable: '+variable
                self.assertIn(variable, dict_row.keys())
            msg = 'every row should have exactly 2 fields'
            num_fields = len( dict_row.keys())
            num_expected = len( list_variables)
            self.assertEqual( num_fields, num_expected, msg)

    def test_selection_defaults(self):
        """
        validate selection REST endpoint parameter: defaults={query_id}
        """
        # check json formatted output
        format_id = 'json'
        source_id = 'trawl.operation_haul_fact'
        bad_defaults_id = 'coreNotARealQuery'
        url = '{}/api/v1/source/{}/selection.{}?year=2015&defaults={}'.format(
            get_base_URI(), source_id, format_id, bad_defaults_id)
        with self.subTest(url=url):
            result = requests.get(url, verify=False)
            # check for error
            self.assertEqual(result.status_code, 400)
            # check header
            self.util_check_p3p_header(result)
            # check error contents
            result_object = result.json()
            expected_headings = {'error', 'data'}
            msg = ('response should consist of DataTables Editor headings,'
                  ' per https://editor.datatables.net/manual/server#Server-'
                  'to-client')
            self.assertEqual(set(result_object.keys()), expected_headings, msg)
            msg = 'response data heading value should be an empty array'
            self.assertEqual(result_object['data'], list(), msg)
            msg = 'response error heading value should contain a title'
            message_title_subheading = 'title'
            self.assertIn(message_title_subheading,result_object['error'], msg)
            msg = 'response error heading value should contain a description'
            message_error_subheading = 'description'
            self.assertIn(message_title_subheading,result_object['error'], msg)
            #check error
            expected_title = 'Invalid parameter'
            self.assertIn(expected_title, result_object['error'])
            expected_description = ( #expect as pprinted Dict
                '{\'description\': \'The "defaults" parameter is invalid.'
                ' Value \'\n                "\'coreNotARealQuery\' is not'
                ' defined for dataset: "\n                "\'trawl.'
                'operation_haul_fact\'",\n \'title\': \'Invalid parameter\'}')
            self.assertIn(expected_description, result_object['error'])
        #TODO: test successful 'core' selection
        #TODO: test successful implicit selection
        #TODO: test successful 'expanded'

    def util_check_pivot_heading(self, column_name, url
                                 ,pivot_dimensional_variable
                                 ,select_fact_variable):
        """
        utility function, to validate pivot column headings

        Keyword Parameters:
        column_name  -- String, representing a pivot column heading
        url  -- String representing RESTful URL used for pivot Selection
        pivot_dimensional_variable  -- String representing the variable
          Selection was pivoted over
        select_fact_variable  -- String, representing the measured Fact
          value included in the selection.
        """
        if select_fact_variable in column_name:
            #Might be a pivot column
            test_pivot = pivot_dimensional_variable in column_name
            msg = ('All column headings containing the data variable'
                   ' name must also include the pivot variable name.'
                   ' URL: {}') 
            self.assertTrue(test_pivot, msg.format(url))
            #Looks good, check for pivot format
            reserved_chars = set(")(")
            valid_variable_chars=(set(pyparsing.printables)-reserved_chars
                                 ).union(' ')
            valid_chars_as_string = ''.join(valid_variable_chars)
            name = lambda: pyparsing.Word(valid_chars_as_string)
            pivot_format = name()+'('+name()+") "+name()+'('+name()+')'
            try:
                parse_output = pivot_format.parseString(
                    column_name
                    ,parseAll=True)
            except Exception as e:
                msg = 'parsing column name: "{}". URL: {}'
                self.assertIsNone(e, msg.format(column_name, url))
            expected_count = 8 #str,(,str,) ,str,(,str,)
            msg = 'parsing column name: "{}". URL: {}'.format(
                parse_output, url)
            self.assertEqual(len(parse_output), expected_count, msg)
            parsed_fact_name = parse_output[0]
            parsed_aggfunc = parse_output[2]
            parsed_pivot_field_name = parse_output[4]
            parsed_pivot_field_value = parse_output[6]
            self.assertEqual(parsed_fact_name, select_fact_variable, msg)
            possible_aggfuncs = ["sum","count"]
            self.assertIn(parsed_aggfunc, possible_aggfuncs, msg)
            self.assertEqual(parsed_pivot_field_name
                              ,pivot_dimensional_variable, msg)
            #... & just check if value is any string(hard to know if valid)
            self.assertIs(type(parsed_pivot_field_value), str, msg)
            return True
        return False

    def test_selection_pivot( self):
        """
        validate Selection REST resource parameter: pivot_columns={vars}
        """
        bad_source_id = 'warehouse.date_dim' #Source is a dimension
        # test pivot
        bad_url = '{}/api/v1/source/{}/selection.{}?pivot_columns={}'.format(
            get_base_URI()
            ,bad_source_id
            ,'json'
            ,None)
        bad_result = requests.get(bad_url, verify=False)
        # check for the expected error
        msg ='Pivot on Dimension should yeild invalid parameter. URL: '
        self.assertEqual(bad_result.status_code, 400, msg+bad_url)

        no_nonpivots = []
        one_nonpivot = ['date_dim$year']
        for select_dimensional_variables in [no_nonpivots, one_nonpivot]:
            # check json formatted output
            format_id = 'json'
            good_source_id = 'hooknline.catch_hooknline_view'
            select_fact_variable = 'total_catch_wt_kg'
            pivot_dimensional_variable = 'common_name'
            # test pivot
            url = ('{}/api/v1/source/{}/selection.{}?pivot_columns={}&variables={}'
                   '&common_name=squarespot rockfish'
                   ',yellowtail rockfish,bocaccio').format(
                get_base_URI()
                ,good_source_id
                ,format_id
                ,pivot_dimensional_variable
                ,','.join([select_fact_variable
                           ,pivot_dimensional_variable]+select_dimensional_variables))
            result = requests.get(url, verify=False)
            # check for error
            self.assertEqual(result.status_code, 200, url)
            # check header
            self.util_check_p3p_header(result)
            # check contents
            result_object = result.json()
            self.assertIsInstance(result_object, list, url)
            result_rows = len(result_object)
            result_columns = result_object[0].keys()
            # check pivot column headings
            # format: 'fact_var(aggFunc) pivot_var(pivot_value)'
            found_pivot_columns = 0
            for column_name in result_columns:
                if self.util_check_pivot_heading(column_name, url
                                                 ,pivot_dimensional_variable
                                                 ,select_fact_variable):
                    found_pivot_columns += 1 #looks good!
                    continue
            msg ='At least 1 column heading must be a pivot field. URL: {}'
            self.assertNotEqual(found_pivot_columns, 0, msg.format(url))
            if select_dimensional_variables:
                for select_dimensional_variable in select_dimensional_variables:
                    # check selected (non-pivot) dimensional field heading
                    msg = ('The non-pivot dimensional test field should be selected'
                           ', verbatim, as a column heading. URL: {}')
                    test = select_dimensional_variable in result_columns
                    self.assertTrue(test, msg.format(url))
            # check column count
            select_dimension_variables_count=len(select_dimensional_variables)
            expected_cols=found_pivot_columns+select_dimension_variables_count
            self.assertEqual(len(result_columns), expected_cols, url)
            # check length
            if not select_dimensional_variables:
                expected_rows = 1
                msg = "pivot is {} row. URL: {}"
                self.assertEqual(result_rows, expected_rows
                               , msg.format(expected_rows,url))
            else:
                expected_rows = 6
                msg = "no dataset's less than {} rows. URL: {}"
                self.assertTrue(result_rows >=expected_rows
                               , msg.format(expected_rows,url))

            # check csv output
            format_id = 'csv'
            # test pivot
            url = ('{}/api/v1/source/{}/selection.{}?pivot_columns={}&variables={}'
                   '&common_name=squarespot rockfish'
                   ',yellowtail rockfish,bocaccio').format(
                get_base_URI()
                ,good_source_id
                ,format_id
                ,pivot_dimensional_variable
                ,','.join([select_fact_variable
                           ,pivot_dimensional_variable]+select_dimensional_variables))
            result = requests.get(url, verify=False)
            # check for error
            self.assertEqual(result.status_code, 200, url)
            # check header
            self.util_check_p3p_header(result)
            # check contents
            result_object = result.content
            self.assertIsInstance( result_object, bytes)
            result_string_iterator = result_object.decode('utf-8-sig').splitlines()
            result_rows = [r for r in csv.reader(result_string_iterator)]
            row_count = len(result_rows)
            result_columns = result_rows[0]
            # check pivot column headings
            # format: 'fact_var(aggFunc) pivot_var(pivot_value)'
            found_pivot_columns = 0
            for column_name in result_columns:
                if self.util_check_pivot_heading(column_name, url
                                                 ,pivot_dimensional_variable
                                                 ,select_fact_variable):
                    found_pivot_columns += 1
                    continue
            msg ='At least 1 column heading must be a pivot field. URL: {}'
            self.assertNotEqual(found_pivot_columns, 0, msg.format(url))
            if select_dimensional_variables:
                for select_dimensional_variable in select_dimensional_variables:
                    # check selected (non-pivot) dimensional field heading
                    msg = ('The non-pivot dimensional test field should be selected'
                           ', verbatim, as a column heading. URL: {}')
                    test = select_dimensional_variable in result_columns
                    self.assertTrue(test, msg.format(url))
            # check column count
            select_dimension_variables_count=len(select_dimensional_variables)
            expected_cols=found_pivot_columns+select_dimension_variables_count
            self.assertEqual(len(result_columns), expected_cols, url)
            # check length
            if not select_dimensional_variables:
                expected_rows = 2 #header row + one data row
                msg = "pivot is {} row. URL: {}"
                self.assertEqual(row_count, expected_rows
                               , msg.format(expected_rows,url))
            else:
                expected_rows = 6
                msg = "no dataset's less than {} rows. URL: {}"
                self.assertTrue(row_count >=expected_rows
                               , msg.format(expected_rows,url))

    def test_selection_empty_cells( self):
        """
        validate Selection REST resource parameter: empty_cells={vars}
        """
        bad_source_id = 'warehouse.date_dim' #Source is a dimension
        # test pivot
        bad_url = '{}/api/v1/source/{}/selection.{}?empty_cells={}'.format(
            get_base_URI()
            ,bad_source_id
            ,'json'
            ,None)
        bad_result = requests.get(bad_url, verify=False)
        # check for the expected error
        msg ='Empty_cells on Dimension should yeild invalid parameter. URL: '
        self.assertEqual(bad_result.status_code, 400, msg+bad_url)

        good_source_id = 'trawl.catch_fact'
        # test pivot
        bad_url = '{}/api/v1/source/{}/selection.{}?empty_cells={}'.format(
            get_base_URI()
            ,good_source_id
            ,'json'
            ,'UnlikelyToBeARealDimensionSG(*STgs4TGT')
        bad_result = requests.get(bad_url, verify=False)
        # check for the expected error
        msg ='Unrecognized Empty_cells value should yeild invalid parameter. URL: '
        self.assertEqual(bad_result.status_code, 400, msg+bad_url)

        # check json formatted output
        format_id = 'json'
        variables = 'vessel,haul_latitude_dim$latitude_in_degree_minute_second,target_station_design_dim$max_depth_m,date_yyyymmdd,best_available_taxonomy_dim$scientific_name,total_catch_numbers'
        filters = 'min_depth_m>=1200,min_depth_m<1200'
        # test non-Empty cells
        url = ('{}/api/v1/source/{}/selection.{}?variables={}'
               '&filters={}').format(
            get_base_URI()
            ,good_source_id
            ,format_id
            ,variables
            ,filters)
        result = requests.get(url, verify=False)
        # check for error
        self.assertEqual(result.status_code, 200, url)
        # check header
        self.util_check_p3p_header(result)
        # check contents
        result_object = result.json()
        self.assertIsInstance(result_object, list, url)
        result_rows = len(result_object)
        expected_rows = 0
        self.assertEqual(result_rows, expected_rows, url)

        #get row count from dimension
        url = ('{}/api/v1/source/{}/selection.{}?variables={}').format(
            get_base_URI()
            ,'warehouse.best_available_taxonomy_dim'
            ,format_id
            ,'scientific_name')
        dim_result = requests.get(url, verify=False)
        # check for error
        self.assertEqual(dim_result.status_code, 200, url)
        # get total # of dimension records
        empty_cell_expected_rows = len(dim_result.json())

        empty_cells = 'best_available_taxonomy_dim'
        # test Empty cell select
        url = ('{}/api/v1/source/{}/selection.{}?empty_cells={}&variables={}'
               '&filters={}').format(
            get_base_URI()
            ,good_source_id
            ,format_id
            ,empty_cells
            ,variables
            ,filters)
        result = requests.get(url, verify=False)
        # check for error
        self.assertEqual(result.status_code, 200, url)
        # check header
        self.util_check_p3p_header(result)
        # check contents
        result_object = result.json()
        self.assertIsInstance(result_object, list, url)
        result_rows = len(result_object)
        self.assertEqual(result_rows, empty_cell_expected_rows, url)

        # test multiple, concurrent "Empty cell" dimensions
        #get row count from the other dimension
        url = ('{}/api/v1/source/{}/selection.{}?variables={}').format(
            get_base_URI()
            ,'warehouse.statistical_partition_dim'
            ,format_id
            ,'partition')
        dim_result = requests.get(url, verify=False)
        # check for error
        self.assertEqual(dim_result.status_code, 200, url)
        # get total # of dimension records
        additional_expected_rows = len(dim_result.json())

        # test multiple Empty cell select
        empty_cells = 'best_available_taxonomy_dim,statistical_partition_dim'
        url = ('{}/api/v1/source/{}/selection.{}?empty_cells={}&variables={}'
               '&filters={}').format(
            get_base_URI()
            ,good_source_id
            ,format_id
            ,empty_cells
            ,variables
            ,filters)
        result = requests.get(url, verify=False)
        # check for error
        self.assertEqual(result.status_code, 200, url)
        # check header
        self.util_check_p3p_header(result)
        # check contents
        result_object = result.json()
        self.assertIsInstance(result_object, list, url)
        result_rows = len(result_object)
        expected_rows = empty_cell_expected_rows+additional_expected_rows
        self.assertEqual(result_rows, expected_rows, url)
