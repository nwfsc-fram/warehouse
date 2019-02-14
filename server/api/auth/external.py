"""Module defining an authentication backend for non-Noaa users

Copyright (C) 2018 ERT Inc.

"""
__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>"
__version__ = "0.1"

import logging

import requests
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError

from api import (
     config_loader
    ,json
)

logger = logging.getLogger(__name__)

domain = "warehouse-external"
# String, representing a X.509 Organization name for non-Noaa users

def oidc_token_to_ldap_style_name(decoded_token):
    """
    Return a NOAA LDAP-style name for the KeyCloak user, as a String

    Keyword Parameters:
    decoded_token  -- Dict, representing the decoded, ODIC token for
      a logged in KeyCloak user

    >>> fake_token = {'jti': None, 'email': 'Pat.Ng@Ertcorp.Com'}
    >>> oidc_token_to_ldap_style_name(fake_token)
    'uid=pat.ng@ertcorp.com,ou=People,o=warehouse-external'
    """
    # Adapt KeyCloak login email, into a LDAP-style name
    user_email = decoded_token['email'].lower()
    generated_ldap_id = 'uid={},ou=People,o={}'.format(user_email, domain)
    return generated_ldap_id

def add_pem_headfoot(public_key):
    """
    Return string, representing PEM text for a public key

    Keyword Parameters:
    public_key  -- String, representing the public key text

    >>> add_pem_headfoot('foo')
    '-----BEGIN PUBLIC KEY-----\\nfoo\\n-----END PUBLIC KEY-----'
    """
    preamble = "-----BEGIN PUBLIC KEY-----\n"
    suffix = "\n-----END PUBLIC KEY-----"
    return preamble+public_key+suffix

class KeycloakBackend:
    """
    KeyCloak ODIC Authentication backend
    """

    @classmethod
    def authenticate(cls, username=None, password=None):
        """
        Return 2tuple, representing authorized user or (None,None) on fail

        First tuple element is String ID representing a distingushed
         name for external users, e.g.:
        "uid=jane.doe@example.tld,ou=People,o=warehouse-external"
        
        Second tuple element is Dict, representing a decoded ODIC access
         token

        >>> b = KeycloakBackend()
        >>> b.authenticate()
        (None, None)
        >>> # Check username
        >>> b.authenticate("brandon.vanvaerenbergh@ertcorp.com", "anything")
        (None, None)
        >>> # Check bogus username
        >>> b.authenticate("Test", "anything")
        (None, None)
        """
        user_identifier = None
        decoded_token = None
        if username is not None:
            u = None #auth may have failed: prepare to return None

            # setup OIDC client
            conf = config_loader.get_api_config()
            auth_url = conf['external.keycloak.url']
            dw_client_id = conf['external.keycloak.warehouse_client_id']
            auth_client = KeycloakOpenID(server_url=auth_url
                ,client_id=dw_client_id, realm_name="master"
                ,client_secret_key="value-doesnt-matter"
                ,verify=False)

            try:
                # login
                encoded_token = auth_client.token(username, password)
                # get server public key
                iss_url = auth_url+'realms/master'
                json_iss = requests.get(iss_url, verify=False).json()
                pub_key = add_pem_headfoot(json_iss['public_key'])
                # decode server response
                decode_opts = {"verify_signature":True, "verify_aud": True, "exp": True}
                decoded_token = auth_client.decode_token(
                     encoded_token['access_token']
                    ,key=pub_key, options=decode_opts)
                user_dn = oidc_token_to_ldap_style_name(decoded_token)
                #login is valid
                user_identifier = user_dn #return
            except KeycloakAuthenticationError:
                pass #login is invalid
        return user_identifier, decoded_token
