"""
Module defining utility functions for API authorization

Copyright (C) 2017-2018 ERT Inc.
"""

def get_user_id(request):
    """
    Returns string representing unique ID for current API session user

    None is returned for anonymous/public API sessions.

    Keyword Parameters:
    request  -- Falcon HTTP request object representing current API call

    >>> from unittest.mock import Mock
    >>> fake_request = Mock()
    >>> fake_request.env = {'beaker.session': {}}
    >>> get_user_id(fake_request) #Check that no session exists
    
    """
    # obtain logged in API user ID (if available)
    try:
        api_session_user = request.env['beaker.session'].get('user_id')
    except KeyError as e:
        api_session_user = None #anonymous user session, no login ID
    # return
    return api_session_user

def create_login_session(user_id, request, saml=None, oidc=None):
    """
    Establishes a Beaker session for the referenced user

    Keyword Parameters:
    user_id  --
    request  -- Falcon HTTP request object representing current API call
    saml  -- Dict, representing attributes of the SAML2 assertion from
      the successful user login (Optional)
    oidc  -- Dict, representing attributes of the decoded, OIDC token
      from the successful user login (Optional)

    >>> from unittest.mock import Mock
    >>> fake_req = Mock()
    >>> fake_req.env = {'beaker.session': {}}
    >>> get_user_id(fake_req) #Check that no session exists
    
    >>> # Check login
    >>> create_login_session('uid=pat.ng,ou=People,o=noaa.gov', fake_req)
    >>> get_user_id(fake_req)
    'uid=pat.ng,ou=People,o=noaa.gov'
    >>> # Check that there is no extra data
    >>> 'saml_assertion_attributes' not in fake_req.env['beaker.session']
    True
    >>> 'oidc_token_attributes' not in fake_req.env['beaker.session']
    True
    >>> # Check extra SAML2 data is added
    >>> fake_req.env = {'beaker.session': {}}
    >>> create_login_session('uid=pat.ng,ou=People,o=noaa.gov', fake_req
    ...                      ,saml={'fake': 'noaa_saml2_info'})
    >>> fake_req.env['beaker.session'].get('saml_assertion_attributes')
    {'fake': 'noaa_saml2_info'}
    >>> 'oidc_token_attributes' not in fake_req.env['beaker.session']
    True
    >>> # Check extra OIDC data is added
    >>> fake_req.env = {'beaker.session': {}}
    >>> create_login_session(
    ...      'uid=pat.ng@ertcorp.com,ou=People,o=warehouse-external'
    ...     ,fake_req
    ...     ,oidc={'jiti': 'fake_uuid'})
    >>> fake_req.env['beaker.session'].get('oidc_token_attributes')
    {'jiti': 'fake_uuid'}
    >>> 'saml_assertion_attributes' not in fake_req.env['beaker.session']
    True
    """
    session = request.env['beaker.session'] #Establish session
    session['user_id'] = user_id #Indicate user is logged in
    if saml:
        #store SAML user assertion
        session['saml_assertion_attributes'] = saml
    if oidc:
        #store ODIC user token
        session['oidc_token_attributes'] = oidc
