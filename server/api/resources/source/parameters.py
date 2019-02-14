"""
Module providing methods to access 'source' RESTful Falcon parameters

Copyright (C) 2016 ERT, Inc.
"""
import falcon

__author__ = "Brandon J. Van Vaerenbergh<brandon.vanvaerenbergh@noaa.gov>, "


source_id = 'source_id'
#String representing Falcon uri parameter (uri path element) for Datasource id

def get_requested_dataset_id(sources, request, resp, params):
    """
    Extracts 'source_id' URL path param, from a Falcon request

    Returns:
    String -- the requested ID

    Exceptions:
    falcon.HTTPNotFound -- raised when no dataset matches the falcon request's
    str_param_id value OR module's 'str_param_id' is not found amongst the
    falcon request's parameters

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> s = [{'id':'trawl.HaulCharsSat', 'name':'One Bogus Source'
    ...       ,'selectable': True}]
    >>> get_requested_dataset_id( s, tr.req, tr.resp, {'source_id': 'trawl.HaulCharsSat'})
    'trawl.HaulCharsSat'
    >>> get_requested_dataset_id( s, tr.req, tr.resp, {'no_id': 'SomethingElse'})
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPNotFound
    >>> get_requested_dataset_id( s, tr.req, tr.resp, {'source_id': 'FooData'})
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPNotFound
    """
    # get identifier, indicating the requested dataset
    try:
        str_requested = params[source_id]
    except KeyError:
        e = falcon.HTTPNotFound(description="No 'source' id specified in URL")
        raise e
    # check if requested dataset is available
    for dict_source in sources:
        if str_requested == dict_source['id']:
            return dict_source['id']
    else:
        raise falcon.HTTPNotFound(description= "No data source by that name: "
                                               + str_requested)
