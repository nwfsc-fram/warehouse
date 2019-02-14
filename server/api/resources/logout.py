"""
Module defining a Falcon resource to terminate login sessions

Copyright (C) 2016 ERT Inc.
"""
import falcon

from api import json

route = "logout"

class Logout():
    """
    Falcon resource object providing API login session termination
    """

    def on_get(self, request, resp):
        """
        terminate API login session
        """
        # Retrieve WSGI session
        session = request.env['beaker.session']

        # Check if there was a login
        try:
            user_id = session['user_id']
        except KeyError:
            user_id = None #no login, still close session though
        # In either case, delete the existing (or empty) session
        session.delete()
        # Return a JSON response
        logout_message = get_logout(user_id)
        json_message = json.dumps(logout_message)
        resp.body = json_message #Return

def get_logout(user_id):
    """
    returns Dict representing a logout response

    Keyword Parameters:
    user_id  -- String, identifying user that was logged out or None if
      the logged out session was a public/anonymous session.

    >>> from pprint import pprint
    >>> # Check arguments
    >>> logout = get_logout()
    Traceback (most recent call last):
       ...
    TypeError: get_logout() missing 1 required positional argument: 'user_id'
    >>> anonymous_logout = get_logout(user_id=None)
    >>> pprint(anonymous_logout)
    {'description': 'Done. No login session found', 'title': 'Session closed'}
    >>> fake_user_id = "uid=bob.newhart,ou=People,o=bobnewhart.com"
    >>> authenticated_logout = get_logout(fake_user_id)
    >>> pprint(authenticated_logout)
    {'description': 'Done. Session logged out for: '
                    'uid=bob.newhart,ou=People,o=bobnewhart.com',
     'title': 'Session closed'}
    """
    title = "Session closed"
    description = "Done. No login session found" #Default
    if user_id is not None:
        description = "Done. Session logged out for: {}".format(user_id)
    message = falcon.HTTPError(status=None, title=title
                               ,description=description).to_dict()
    return message
