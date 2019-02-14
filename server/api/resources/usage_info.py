"""
Module, defining a Falcon resource providing documentation on API usage

Copyright (C) 2016 ERT Inc.
"""
import os.path
import logging

import falcon
import grip

route = 'help'
#string, representing RESTful endpoint name for this resource

documentation_folder = 'doc'
#string, representing WSGI application root folder name with API docs

documentation_filename = 'Client API.md'
#string representing name of 'documentation_folder' file with usage info

help_path = os.path.join(documentation_folder, documentation_filename)
#file path, to file with API usage info

logger = logging.getLogger(__name__)
#logger, for this module

embed_css_in_html = True
help_html = grip.render_page(path=help_path, render_inline=embed_css_in_html)

class Help:
    """
    Falcon resource object, providing API documentation
    """

    def on_get(self, request, resp, **kwargs):
        """
        Falcon resource method providing documentation
        """
        resp.content_type = 'text/html; charset=utf-8'
        resp.body = help_html
