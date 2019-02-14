"""
Module defining a FRAM Json serializer for use with Python json.dumps function

Copyright (C) 2015, 2016 ERT Inc.
"""
import simplejson as json #Using simplejson until https://bugs.python.org/issue16535 resolved
import numpy #defining default_fram rule, until https://bugs.python.org/issue24313 resolved

from datetime import datetime, date, time

__author__ = 'Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, '

def default_fram( object_to_serialize):
    """
    Python json api custom serializer function for FRAM Warehouse API

    per:'Specializing JSON object encoding', https://simplejson.readthedocs.org
    
    >>> import simplejson as json
    >>> json.dumps({'Without':[1,'a',datetime(1999, 1, 1),'Serializer']})
    Traceback (most recent call last):
      ...
    TypeError: datetime.datetime(1999, 1, 1, 0, 0) is not JSON serializable
    >>> dict2 = {'With':[1,'a',datetime(1999, 1, 1),'Serializer']}
    >>> json.dumps( dict2, default=default_fram)
    '{"With": [1, "a", "1999-01-01T00:00:00Z", "Serializer"]}'
    >>> dict3 = {'With':[1,'a',date(1999, 1, 1),'Serializer']}
    >>> json.dumps( dict3, default=default_fram)
    '{"With": [1, "a", "1999-01-01", "Serializer"]}'
    >>> dict4 = {'With':[1,'a',time(4, 5, 6),'Serializer']}
    >>> json.dumps( dict4, default=default_fram)
    '{"With": [1, "a", "1970-01-01T04:05:06Z", "Serializer"]}'
    >>> numpy_64bit_int = {'With':[1,numpy.int64(5678),'Support']}
    >>> json.dumps(numpy_64bit_int, default=default_fram)
    '{"With": [1, 5678, "Support"]}'
    >>> numpy_32bit_int = {'With':[1,numpy.int32(5678),'Support']}
    >>> json.dumps(numpy_64bit_int, default=default_fram)
    '{"With": [1, 5678, "Support"]}'
    >>> numpy_16bit_int = {'With':[1,numpy.int16(5678),'Support']}
    >>> json.dumps(numpy_64bit_int, default=default_fram)
    '{"With": [1, 5678, "Support"]}'
    """
    #Bake datetime objects into Strings
    if isinstance( object_to_serialize, datetime):
        if object_to_serialize.utcoffset() is None:
            #Append 'Z', to conform to ISO8601 date spec
            return object_to_serialize.isoformat()+'Z'
        #Else, TZ offset present. TZ info will be automatically included per
        # docs.python.org/3/library/datetime.html#datetime.datetime.isoformat
        return object_to_serialize.isoformat()
    if isinstance( object_to_serialize, date):
        # No Timezone info available,
        return object_to_serialize.isoformat()
    if isinstance( object_to_serialize, time):
        #No date available.Prefix:'1970-01-01T',to conform to ISO8601 date spec
        isoformat = '1970-01-01T'+object_to_serialize.isoformat()
        if object_to_serialize.utcoffset() is None:
            # No Timezone info available,
            # Append 'Z',to conform to ISO8601 date spec
            return isoformat+'Z'
        #else, TZ offset has already been added to string.
        return isoformat
    if isinstance(object_to_serialize, numpy.integer):
        return int(object_to_serialize) #per Python issue24313, no support for numpy Ints
    #Else, wasnt a datetime Date & we dont handle anything else.. so:
    raise TypeError(repr(object_to_serialize) + " is not JSON serializable")

def dumps(object_to_serialize, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=None, separators=None, default=default_fram, sort_keys=False, **kw):
    """
    Serialize obj to a JSON formatted str using this conversion table. The arguments have the same meaning as in dump().

    per: https://docs.python.org/3/library/json.html#json.dumps

    >>> dumps({'Great':[1,'b','Job']})
    '{"Great": [1, "b", "Job"]}'
    >>> from datetime import datetime
    >>> dumps({'Great':[1,datetime(1999, 1, 1),'Job']})
    '{"Great": [1, "1999-01-01T00:00:00Z", "Job"]}'
    """
    return json.dumps(object_to_serialize, skipkeys=skipkeys, ensure_ascii=ensure_ascii, check_circular=check_circular, allow_nan=allow_nan, cls=cls, indent=indent, separators=separators, default=default, sort_keys=sort_keys, **kw)

class JSONEncoder(json.JSONEncoder):
    """
    default_fram custom extensible JSON encoder for Python objects

    All other arguments have the same meaning as in dump()
    per: https://docs.python.org/3/library/json.html#json.JSONEncoder

    >>> testme = JSONEncoder()
    >>> out = testme.iterencode({'Great':[1,'b','Job']})
    >>> ''.join(out)
    '{"Great": [1, "b", "Job"]}'
    >>> from datetime import datetime
    >>> out = testme.iterencode({'Great':[1,datetime(1999, 1, 1),'Job']})
    >>> ''.join(out)
    '{"Great": [1, "1999-01-01T00:00:00Z", "Job"]}'
    """
    def __init__(self, **kwargs):
        if ('default' not in kwargs
                or kwargs['default'] is None):
            kwargs['default'] = default_fram #apply custom serialization rules
        super().__init__(**kwargs)

#transparently expose a few useful JSON library functions here,w/ no alteration
loads = json.loads
load = json.load
