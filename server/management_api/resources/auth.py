"""
Module defining utility functions for sensitive Selection authorization

Copyright (C) 2017 ERT Inc.
"""

def is_management_permitted(user_id, dwsupport_model):
    """
    Return true if User has been authorized to manage DWSupport config

    Keyword Parameters:
    user_id  -- String, representing unique identifier for user that 
      initiated the authorized API session.
    dwsupport_model  -- Dictionary of lists, representing DWSupport and
      DWAuth configuration.

    >>> test_id = 'uid=salvadore.dali,ou=People,o=noaa.gov'
    >>> test_model = {'table_authorizations': [
    ...     {'user_id': test_id, 'table': 'thank_you_notes_fact'
    ...      ,'project': 'mail'}
    ...     ,{'user_id': test_id, 'table': 'bills_fact', 'project': 'mail'}
    ... ]
    ... ,'management_authorizations': [{'user_id': test_id}]}
    >>> # Check management access
    >>> is_management_permitted(test_id, test_model)
    True
    >>> # Check access when authorization list is empty
    >>> test_model['management_authorizations'] = []
    >>> is_management_permitted(test_id, test_model)
    False
    """
    # get authorizations
    for authorization in dwsupport_model['management_authorizations']:
        if authorization['user_id'] == user_id:
           return True
    #otherwise, unauthorized
    return False
    
