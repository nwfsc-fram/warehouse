"""
Module defining utility functions for sensitive Selection authorization

Copyright (C) 2016-2017 ERT Inc.
"""

def is_select_permitted(user_id, table, dwsupport_model):
    """
    Return true if User has been authorized to select from 'table'

    Keyword Parameters:
    user_id  -- String, representing unique identifier for user that 
      initiated the authorized API session.
    table  -- DWSupport Data Transfer Object representing the warehouse
      table the user would like to access.
    dwsupport_model  -- Dictionary of lists, representing DWSupport and
      DWAuth configuration.

    >>> test_id = 'uid=salvadore.dali,ou=People,o=noaa.gov'
    >>> test_model = {'table_authorizations': [
    ...     {'user_id': test_id, 'table': 'thank_you_notes_fact'
    ...      ,'project': 'mail'}
    ...     ,{'user_id': test_id, 'table': 'bills_fact', 'project': 'mail'}
    ... ]}
    >>> allowed_table = {'name': 'thank_you_notes_fact', 'project': 'mail'}
    >>> # Check access to an authorized table
    >>> is_select_permitted(test_id, allowed_table, test_model)
    True
    >>> unauthorized_table = {'name': 'summons_fact'
    ...                      ,'project': 'mail'}
    >>> # Check access to another project table
    >>> is_select_permitted(test_id, unauthorized_table, test_model)
    False
    >>> different_project = {'name': 'thank_you_notes_fact'
    ...                     ,'project': 'pats_unset_stationary'}
    >>> # Check access to table with same name as an authorized table
    >>> is_select_permitted(test_id, different_project, test_model)
    False
    >>> # Check access when authorization list is empty
    >>> no_auths = {'table_authorizations': []}
    >>> is_select_permitted(test_id, allowed_table, no_auths)
    False
    """
    # tuple, representing the requested resource
    requested_tuple = (table['project'], table['name'])

    # get authorizations
    user_authorization_tuples = []
    for authorization in dwsupport_model['table_authorizations']:
        if authorization['user_id'] == user_id:
            # build a tuple, for each resource user's authorized to read
            authorized_project_table_tuple = (
                authorization['project'], authorization['table']
            )
            user_authorization_tuples.append(authorized_project_table_tuple)

    if requested_tuple in user_authorization_tuples:
        return True
    #otherwise, unauthorized
    return False
    
