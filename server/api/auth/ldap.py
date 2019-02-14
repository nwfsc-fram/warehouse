"""Module defining generic authentication backend for NOAA LDAP

Copyright (C) 2016, 2018 ERT Inc.

"""
__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>"
__version__ = "0.2"

import os.path
import ssl
import logging

from ldap3 import (
    Tls
    ,Server
    ,Connection
)
from ldap3.core.exceptions import (
    LDAPInvalidCredentialsResult
    ,LDAPNoSuchObjectResult
    ,LDAPBusyResult
    ,LDAPException
)

logger = logging.getLogger(__name__)

LDAP_WEST = 'ldaps://ldap-west.nems.noaa.gov:636'
LDAP_MOUNTAIN = 'ldaps://ldap-mountain.nems.noaa.gov:636'
LDAP_EAST = 'ldaps://ldap-east.nems.noaa.gov:636'

class LdapBusy(RuntimeError):
    # raised when all configured LDAP servers are unavailable
    pass

class LdapFailure(RuntimeError):
    # raised when all configured LDAP servers return errors
    pass

class LdapBackend:
    """
    Generic Authentication backend
    """

    @classmethod
    def authenticate(cls, username=None, password=None):
        """
        Return String id for authorized users or None if login fails

        String ID represents the Users LDAP distingushed name, e.g.:
        "uid=Jane.Doe,ou=People,o=noaa.gov"

        Keyword arguments:
        username --  String representing NOAA username e.g.: "jane.doe"
          (Do not prefix the username value with domain info, e.g.:
           "FRAM/jane.doe", etc.)
        password --  String representing user password

        Exceptions:
        LdapFailure --  NOAA West, Mountain, & East LDAP servers all
          return an error/unavailable
        LdapBusy --  Connections failed but at least one NOAA LDAP
          server returned LDAPBusyResult

        >>> b = LdapBackend()
        >>> b.authenticate()
        
        """
        user_identifier = None
        if username is not None:
            u = None #auth may have failed: prepare to return None
            user_dn = 'uid={0},ou=People,o=noaa.gov'.format(username)

            # validate LDAP server is authentic, before sending the user's PW
            module_path = os.path.dirname(__file__)
            ldap_tls_context = Tls(
                ca_certs_file=os.path.join(module_path, "noaa-ldap-certs.crt")
                ,validate=ssl.CERT_REQUIRED
                ,ciphers='ECDHE-RSA-AES256-SHA384:AES256-SHA:RC4-MD5:DES-CBC3-SHA' #LDAP server supports both 128bit RC4 and SSL_RSA_WITH_3DES_EDE_CBC_SHA (AES256 ciphers added with TLSv1.2)
            )
            # NOAA LDAP servers, nearest to NWFSC (geographically) to furthest
            ldap_servers = (# set comprehension,of three ldap3 'Server' objects
                Server(url, use_ssl=True, tls=ldap_tls_context)#force SSL usage
                for url
                in (LDAP_WEST, LDAP_MOUNTAIN, LDAP_EAST) # 3x urls (in order)
            )

            # try 3x NOAA LDAP servers in sequence, until one works.
            conn_args = {
                'password': password
                ,'auto_bind': True #Immediately try & authenticate
                ,'raise_exceptions': True#raise LDAPOperationResult subclasses
                ,'receive_timeout': 10#wait seconds,then try next server
            }
            failures = [] # track failure reasons
            busy = False # track if server was just busy
            for server in ldap_servers:
                try:
                    connection = Connection(server, user_dn, **conn_args)
                    connection.unbind()
                    #login is valid
                    user_identifier = user_dn #return
                    break
                except LDAPNoSuchObjectResult:
                    #login is invalid (Unrecognized username)
                    break
                except LDAPInvalidCredentialsResult:
                    #login is invalid
                    break
                except LDAPBusyResult as e:
                    failures.append(e)
                    logging.warning(e)
                    busy = True
                except LDAPException as e:
                    # last, catch all other exceptions, log & retry
                    failures.append(e)
                    logging.warning(e)
            else:
                failure3, failure2, failure1 = (failures.pop()
                                                ,failures.pop()
                                                ,failures.pop())
                failure3.__cause__ = failure2 # explicit chaining, per PEP-3134
                failure2.__cause__ = failure1
                if busy:
                    raise LdapBusy() from failure3
                # else, no servers were busy
                raise LdapFailure() from failure3
        return user_identifier
