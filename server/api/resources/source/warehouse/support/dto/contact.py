"""
Module, providing a DAO api for accessing metadata on warehoused contacts

Copyright (C) 2016 ERT Inc.
"""
from api.resources.source.warehouse.support import (
    dto_util
)

TABLE = "contact"
# Warehouse table,containing the warehouse contacts

class ValidateTypeError(TypeError):
    """
    Type of a Warehouse contact is not a string
    """
    pass
class ValidateUnexpectedValue(ValueError):
    """
    Length of Warehouse contact is greater than 800 or less than 2
    """
    pass

def get_all(db_url=None, connection_func=None):
    """
    returns list of all Warehouse contacts

    Keyword Parameters:
    db_url  --  String, representing a SQLAlchemy connection (Required, if
      parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ConnectionMissingArgument  -- raised if neither connection or db_url parameter
      is specified.
    ValidateException -- raised when a problem is encountered validating a dto

    >>> get_all()
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ConnectionMissingArgument
    """
    # get db connection
    connection = dto_util.get_connection( db_url, connection_func)
    # prepare statement, to get project metadata
    select_statement = ('SELECT \n'
                        '   c.info \n'
                        'FROM {schema}.{table} c \n'
                       ).format(schema=dto_util.SCHEMA, table=TABLE)
    try:
        result = connection.execute(select_statement)
        contacts = list()
        for row in result:
            contacts.append(row['info'])
        return contacts
    except:
        raise
    finally:
        connection.close()

def validate(contact):
    """
    validate if object conforms to module's api for warehouse contacts

    Keyword Parameters:
    contact -- String, representing a warehouse contact

    Exceptions:
    ValidateTypeError -- raised when contact is not a String
    ValidateValueError -- raised when contact info is more than 800 char

    >>> validate('float')
    True
    >>> validate('Name: Amazing Pat <pat.a@example.domain> Office: N/A')
    True
    >>> validate({'python_type':'dict'})
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.contact.ValidateTypeError: <class 'dict'>
    >>> too_short = 'N'
    >>> validate(too_short)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.contact.ValidateUnexpectedValue: N
    >>> too_long = '!'*801
    >>> validate(too_long)
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto.contact.ValidateUnexpectedValue: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    """
    # verify object type
    if not isinstance(contact, str):
        raise ValidateTypeError(type(contact))
    # verify object contents
    max_length = 800
    if len(contact) > max_length:
        raise ValidateUnexpectedValue(contact)
    min_length = 2
    if len(contact) < min_length:
        raise ValidateUnexpectedValue(contact)
    # must be good!
    return True

def save(contacts, db_url=None, connection_func=None):
    """
    persists a list of one (or more) contacts, to the warehouse database

    Keyword Parameters:
    contacts  --  list of contacts
    db_url  --  String, representing a SQLAlchemy connection (Required,
      if parameter 'connection' is not provided.
    connection_func  -- function returning SQLAlchemy connections
      (Optional, if provided, will override db_url)

    Exceptions:
    ExecMissingArguments  -- raised if neither connection or db_url
      parameter is specified.
    ValidateException -- raised when a problem is encountered validating
      a dto

    >>> empty_list = []
    >>> save([])
    Traceback (most recent call last):
       ...
    api.resources.source.warehouse.support.dto_util.ExecMissingArgument
    """
    # prepare statement, to write out the contacts metadata
    template = ('INSERT into {schema}.{table} ( \n'
                '  info ) values ( \n'
                '  %s \n'
                ' )')
    insert_statement = template.format(schema=dto_util.SCHEMA, table=TABLE)
    # insert!
    dto_util.exec_base(contacts, validate, insert_statement, db_url=db_url
                       ,connection_func=connection_func)
