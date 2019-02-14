"""
Module defining a Falcon resource to provide login session info

Copyright (C) 2016 ERT Inc.
"""
import falcon

import api.json as json
from api.auth import auth

route = "user"

class User():
    """
    Falcon resource object providing API login session info
    """

    def on_get(self, request, resp):
        """
        return JSON object, representing the current session's user info
        """
        user_id = auth.get_user_id(request)
        # return JSON user representation
        user = get_user(user_id)
        json_user = json.dumps(user)
        resp.body = json_user

def get_user(user_id=None):
    """
    Return object representing the logged in user

    Keyword Parameters:
    user_id  -- String, identifier representing the logged in user
      (Default: None, representing an public/anonymous user session)

    >>> # Check public/Anonymous user
    >>> from pprint import pprint
    >>> anonymous_user = get_user()
    >>> pprint(anonymous_user)
    {'user': {'description': 'Anonymous user.', 'id': None}}
    >>> anonymous_user = get_user(None) #public/Anonymous user
    >>> pprint(anonymous_user)
    {'user': {'description': 'Anonymous user.', 'id': None}}
    >>> # Check logged in user
    >>> user = get_user('uid=bob.newhart,ou=People,o=bobnewhart.com')
    >>> pprint(user)
    {'user': {'description': 'Authenticated user.',
              'id': 'uid=bob.newhart,ou=People,o=bobnewhart.com'}}
    """
    description = "Authenticated user."
    if user_id is None:
        description = "Anonymous user."
    attributes = {'id': user_id, 'description': description}
    user_object = {'user': attributes}
    return user_object
