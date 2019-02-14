"""
Module defining Falcon resource, for the API's P3P Policy Reference File

Copyright (C) 2016 ERT Inc.
"""
import falcon

from api import config_loader

str_route = 'p3p.xml'
"""
String representing the URI path for this endpoint

E.g., "/p3p.xml"
"""

reference_file_name = 'p3p.xml'
# String, representing the name of server/ file with Policy Reference template

#Load once, at app startup
xml_text = open(config_loader.get_server_file_path(reference_file_name)).read()

class PolicyReferenceFile:
    """
    Falcon resource object, representing the API's Policy Reference File
    """

    def on_get(self, request, resp, **kwargs):
        """
        Falcon resource method, for handling HTTP request GET method

        Falcon request provides: parameters embedded in URL via a keyword args
        dict, as well as convenience class variables falcon.HTTP_*
        """
        # text sourced from: http://www.nwfsc.noaa.gov/w3c/p3p.xml
        resp.content_type = 'text/xml'
        resp.body = xml_text
