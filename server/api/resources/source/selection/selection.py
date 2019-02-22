# pylint: disable=too-many-statements
"""
Module providing an RESTful endpoint, representing Observer species counts

Copyright (C) 2015-2017 ERT Inc.
"""
import csv
import io
import codecs
from datetime import datetime
import pytz

import falcon
import xlsxwriter

import api.json as json
from api.auth import auth
from api.resources.source import (
    source
    ,parameters as source_parameters
    ,variables
)
from api.resources.source.data import data
from . import (
     parameters
    ,defaults
    ,streaming
)
from api.resources.source.warehouse import warehouse
import sqlalchemy.exc #DatabaseError

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

str_route = 'selection.'
"""
String representing the URI path for this endpoint

E.g., "/selection.{type}"
"""

str_param_type = 'type'
#String representing Falcon uri parameter for desired response format

class Selection:
    """
    A Falcon resource object, representing a FRAM dataset subselection
    """

    def on_get(self, request, resp, **kwargs):
        """
        Falcon resource method, for handling HTTP request GET method

        Falcon request provides: parameters embedded in URL via a keyword args
        dict, as well as convenience class variables falcon.HTTP_*

        FIXME: remove moduel pylint:disable= & refactor this overlong code block!
        """
        # obtain logged in API user ID (if available)
        api_session_user = auth.get_user_id(request)
        # select data
        with warehouse.get_source_model_session() as dwsupport_model:
            sources = source.SourceUtil.get_list_of_data_sources(
                 request.url
                ,auth.get_user_id(request)
                ,dwsupport_model)
            str_dataset_id = get_requested_dataset_id( sources, request, resp, kwargs)
            list_variables_requested_source = variables.get_list_of_variables( str_dataset_id)
            # convert 'datasets' into a list of variables
            list_requested_datasets = parameters.get_requested_datasets( request)
            list_variables_from_datasets = []
            for str_id in list_requested_datasets:
                if str_dataset_id == str_id:
                    list_variables_from_datasets = list_variables_requested_source
                    break
                if str_dataset_id == 'warehouse': #FIXME: refactor this into a source.warehouse function
                    #obtain the 'warehouse' field aliases for each dataset
                    list_source_variables = variables.get_list_of_variables( str_id)
                    for var in list_source_variables:
                        warehouse_utils = api.resources.source.warehouse.warehouse
                        str_alias = warehouse_utils.prefix_field_name( var, str_id)
                        list_variables_from_datasets.append( str_alias)
                else: #error; not a warehouse request & Dataset does not match requested ID
                    raise falcon.HTTPNotFound(description= "Unrecognized dataset: "
                                           + str_id)
            list_requested_variables = parameters.get_requested_variables( request)

            # add default variables
            if len(list_requested_variables) < 1:
                requested_default_query = parameters.get_list_requested_parameter(
                    defaults.PARAMETER_NAME, request)
                try:
                    default_variables = defaults.get_default_variables(
                         requested_default_query
                        ,str_dataset_id
                        ,dwsupport_model)
                except defaults.UndefinedDefaultQuery as error:
                    msg = ("Value {} is not defined for dataset: '{}'"
                           .format(error, str_dataset_id))
                    raise falcon.HTTPInvalidParam(msg, defaults.PARAMETER_NAME)
                except defaults.AmbiguousDefaultQuery as error:
                    msg = "More than one value was specified: {}".format(error)
                    raise falcon.HTTPInvalidParam(msg, defaults.PARAMETER_NAME)
                except defaults.AmbiguousQueryHierarchy as error:
                    raise falcon.HTTPBadRequest( #TODO: add functional test coverage
                        title="Missing Parameter"
                        ,description=(
                           "Selection defaults not clear for"
                           " data source: '{}'."
                           " Selection must specify one or more 'variables='"
                           " selection parameters (or a 'defaults=' parameter"
                           " value from the following list: {})"
                           ).format(str_dataset_id, error)
                    )
                list_requested_variables.extend(default_variables)

            # add variables derived from 'datasets' param
            list_requested_variables.extend( list_variables_from_datasets)
            list_requested_filters = parameters.get_requested_filters( request)
            # process pivot columns parameter
            try:
                pivot_column_variables = parameters.get_requested_pivot_columns(
                    request
                    ,str_dataset_id
                    ,dwsupport_model['tables'])
            except parameters.PivotVariableError as err:
                raise falcon.HTTPInvalidParam(
                    msg=str(err)
                    ,param_name=parameters.ReservedParameterNames.pivot_columns
                ) from err
            # process 'Empty_cells' parameter
            try:
                empty_cell_dimensions = parameters.get_requested_empty_cells(
                    request
                    ,str_dataset_id
                    ,dwsupport_model['tables']
                    ,dwsupport_model['associations']
                )
            except (parameters.EmptyCellsSourceError
                    ,parameters.EmptyCellsDimensionError) as err:
                raise falcon.HTTPInvalidParam(
                    msg=str(err)
                    ,param_name=parameters.ReservedParameterNames.empty_cells
                ) from err
            # retrieve data
            start_time = datetime.now(pytz.timezone('US/Pacific'))
            try:
                result_generator = data.get_data(str_dataset_id
                                            ,list_requested_variables
                                            ,list_requested_filters
                                            ,pivot_column_variables
                                            ,empty_cell_dimensions
                                            ,user_id=api_session_user)
            except sqlalchemy.exc.DatabaseError as err:
                raise falcon.HTTPInternalServerError(
                    title='500'
                    ,description="Please try again"
                ) from err
            except data.NoSourceException as err:
                raise falcon.HTTPNotFound(description=("Source '{}' dataset not found:"
                                                       " {}").format(str_dataset_id,err)) from err
            except parameters.FilterVariableError as err:
                #TODO: the bad HTTP parameter not always 'filters',sometimes a user-defined param (implicit-filter)
                #TODO: perhaps parameters should raise two different Exceptions?
                raise falcon.HTTPInvalidParam(str(err), 'filters') from err
            except data.NotAuthorizedException as error:
                raise falcon.HTTPUnauthorized(
                    title='401'
                    ,description=("Selection from sensitive data source '{}'"
                                  " not authorized").format(str_dataset_id)
                ) from error
            str_format_type = get_requested_format_type( kwargs)
            resp.content_type = FormatUtil.get_http_content_type(str_format_type)
            for data_source in sources:
                if data_source['id'] == str_dataset_id:
                    formatter = FormatUtil(str_format_type, data_source, request, start_time)
                    result_stream = formatter.format(result_generator)
                    break
            chunked_stream = streaming.biggerchunks_stream(result_stream, 4)#2(13.6),3(13),4(
            if str_format_type == 'xlsx':
                byte_stream = chunked_stream #already bytes
            else:
                encoding = 'utf-8'
                if resp.content_type == 'text/csv':
                    encoding = 'utf-8-sig'
                byte_stream = codecs.iterencode(chunked_stream, encoding)
            resp.stream = byte_stream#content

class FormatUtil:
    """
    Class encapsulating selection formatting functions

    >>> # Example usage 1
    >>> FormatUtil.get_http_content_type('csv')
    'text/csv'
    >>> # Check formats
    >>> FormatUtil.get_format_ids()
    ['csv', 'json', 'xlsx']
    >>> # Example usage 2 -- format() method
    >>> from unittest.mock import Mock
    >>> data_source = {'id': 'my.fake', 'description': 'Great data'}
    >>> fake_req = Mock()
    >>> fake_req.uri = 'https://example.domain/api/v1/source/my.fake/selection.json'
    >>> time = datetime.now()
    >>> def test_results_generator():
    ...     yield ('foo', 'bar', 'data')
    ...     yield (1, 2, 42)
    >>> formatter = FormatUtil('json', data_source, fake_req, time)
    >>> output = formatter.format(test_results_generator())
    >>> ''.join(output)#consume iterator & concat returned strings
    '[{"bar": 2, "data": 42, "foo": 1}]'
    """
    def __init__(self, format_id, data_source, request, start_time):
        """
        Keyword Parameters:
        format_id  -- String, identifying the the output format
        data_source  -- Dict, representing the data source result was retrieved from
        request  -- Falcon Request object representing this HTTP request
        start_time  -- datetime representing the time result was retrieved

        Exceptions:
        falcon.error.HTTPNotFound -- raised when referenced format type is
            unrecognized.

        >>> from unittest.mock import Mock
        >>> data_source = {'id': 'my.fake', 'description': 'Great data'}
        >>> fake_req = Mock()
        >>> fake_req.uri = 'https://example.domain/api/v1/source/my.fake/selection.json'
        >>> time = datetime.now()
        >>> formatter = FormatUtil('json', data_source, fake_req, time)
        >>> formatter.data_source
        {'id': 'my.fake', 'description': 'Great data'}
        >>> FormatUtil('fizzbuzz', data_source, fake_req, time)
        Traceback (most recent call last):
          ...
        falcon.errors.HTTPNotFound
        """
        self.format_id = format_id
        try:
            lower_trimmed_id = format_id.strip().lower()
            # get the dict, which contains our formatting function
            format_info = self.format_dicts_by_type[lower_trimmed_id]
        except KeyError as e:
            raise falcon.HTTPNotFound(description= "Unrecognized format type: "
                                                   + format_id)
        self.format_info = format_info
        self.data_source = data_source
        self.request = request
        self.start_time = start_time

    @classmethod
    def get_format_ids(cls):
        """
        Return list of sorted string format names

        >>> FormatUtil.get_format_ids()
        ['csv', 'json', 'xlsx']
        """
        formats = list(cls.format_dicts_by_type)
        formats.sort()
        return formats

    def format(self, results):
        """
        Return String generator, yielding formatted dataset selection

        Keyword Parameters:
        results  -- Generator yielding a tuple representing data field
          names, followed by additional tuples representing data rows

        >>> from unittest.mock import Mock
        >>> data_source = {'id': 'my.fake', 'description': 'Great data'}
        >>> fake_req = Mock()
        >>> fake_req.uri = 'https://example.domain/api/v1/source/my.fake/selection.json'
        >>> time = datetime.now()
        >>> formatter = FormatUtil('json', data_source, fake_req, time)
        >>> def test_generator1():
        ...     raise StopIteration()
        ...     yield False #impossible
        >>> out = formatter.format(test_generator1())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> ''.join(out)#consume iterator & concat returned strings
        '[]'
        >>> def test_generator2():
        ...     yield ('foo', 'bar', 'data')
        ...     yield (1, 2, 42)
        >>> out = formatter.format(test_generator2())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> ''.join(out)#consume iterator & concat returned strings
        '[{"bar": 2, "data": 42, "foo": 1}]'
        >>> def test_generator3():
        ...     yield ('a', 'z', 'b')
        ...     yield (1, 26, 2)
        ...     yield (3, 28, 4)
        >>> out = formatter.format(test_generator3())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> ''.join(out)#consume iterator & concat returned strings
        '[{"a": 1, "b": 2, "z": 26}, {"a": 3, "b": 4, "z": 28}]'
        """
        description = self.data_source['description']
        url = self.request.uri
        # retrieve the formatting function, from the dict
        format_function = self.format_info['function']
        return format_function(self, results)

    def _format_csv(self, results):
        """
        Utility function, CSV format a dataset Selection

        Keyword Parameters:
        results  -- Generator yielding a header tuple & tuples of data

        Returns:
        String generator -- formatted dataset selection

        >>> from unittest.mock import Mock
        >>> data_source = {'id': 'my.fake', 'description': "Great data"}
        >>> fake_req = Mock()
        >>> fake_req.uri = "https://example.domain/api/v1/source/my.data/selection.csv"
        >>> time = datetime.now(pytz.timezone('US/Pacific'))
        >>> formatter = FormatUtil('csv', data_source, fake_req, time)
        >>> def test_generator1():
        ...     raise StopIteration()
        ...     yield False #impossible
        >>> out = formatter._format_csv(test_generator1())
        >>> ''.join(out)#consume iterator & concat returned strings
        '\\r\\n'
        >>> def test_generator2():
        ...     yield ('foo', 'bar', 'data')
        ...     yield (1, 2, 42)
        >>> out = formatter._format_csv(test_generator2())
        >>> ''.join(out)#consume iterator & concat returned strings
        '"bar","data","foo"\\r\\n"2","42","1"\\r\\n'
        >>> def test_generator3():
        ...     yield ('a', 'z', 'b')
        ...     yield (1, 26, 2)
        ...     yield (3, 28, 4)
        >>> out = formatter._format_csv(test_generator3())
        >>> ''.join(out)#consume iterator & concat returned strings
        '"a","b","z"\\r\\n"1","2","26"\\r\\n"3","4","28"\\r\\n'
        >>> def test_generator4():
        ...     yield ('foo', 'bar', 'data')
        >>> out = formatter._format_csv(test_generator4())
        >>> ''.join(out)#consume iterator & concat returned strings
        '"bar","data","foo"\\r\\n'
        """
        string_stream_output = io.StringIO()
        bool_sort_keys=True
        # extract the first set (header row) from the list of sets& write to buffer
        try:
            tuple_header_unsorted = next(results)
            list_header = list(tuple_header_unsorted)
            if bool_sort_keys:
                list_header.sort()
        except StopIteration: #No results! No formatting needed
            writer = csv.DictWriter( string_stream_output, fieldnames=[], quoting=csv.QUOTE_ALL)
            writer.writeheader()
            yield string_stream_output.getvalue()
            raise StopIteration()

        writer = csv.DictWriter( string_stream_output, fieldnames=list_header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        yield string_stream_output.getvalue()

        # convert the list of remaining sets to dicts, and write to buffer
        while True:
            set_row = next(results)
            # build a dict; representing this rows's values, plus the header info
            dict_row = {}
            # add each element of the set to dict, using header value as key
            for index_header, str_header in enumerate(tuple_header_unsorted):
                dict_row[str_header] = set_row[index_header]
            # yield new row string
            string_stream_output = io.StringIO()
            writer = csv.DictWriter(string_stream_output, fieldnames=list_header, quoting=csv.QUOTE_ALL)
            writer.writerow(dict_row)
            yield string_stream_output.getvalue()

    def _format_json(self, results):
        """
        Utility function, JSON format a dataset Selection

        Keyword Parameters:
        results  -- Generator yielding a header tuple & tuples of data

        Returns:
        String generator -- formatted dataset selection

        >>> from unittest.mock import Mock
        >>> data_source = {'id': 'my.fake', 'description': "Great data"}
        >>> fake_req = Mock()
        >>> fake_req.uri = "https://example.domain/api/v1/source/my.data/selection.json"
        >>> time = datetime.now(pytz.timezone('US/Pacific'))
        >>> formatter = FormatUtil('json', data_source, fake_req, time)
        >>> def test_generator1():
        ...     raise StopIteration()
        ...     yield False #impossible
        >>> out = formatter._format_json(test_generator1())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> ''.join(out)#consume iterator & concat returned strings
        '[]'
        >>> def test_generator2():
        ...     yield ('foo', 'bar', 'data')
        ...     yield (1, 2, 42)
        >>> out = formatter._format_json(test_generator2())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> ''.join(out)#consume iterator & concat returned strings
        '[{"bar": 2, "data": 42, "foo": 1}]'
        >>> def test_generator3():
        ...     yield ('a', 'z', 'b')
        ...     yield (1, 26, 2)
        ...     yield (3, 28, 4)
        >>> out = formatter._format_json(test_generator3())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> ''.join(out)#consume iterator & concat returned strings
        '[{"a": 1, "b": 2, "z": 26}, {"a": 3, "b": 4, "z": 28}]'
        """
        bool_sort_keys=True
        # extract the first set (header row) from the list of sets
        try:
            tuple_header = next(results)
        except StopIteration: #No results! No formatting needed
            string_stream = json.JSONEncoder(sort_keys=bool_sort_keys).iterencode([])
            return string_stream
        # convert the list of remaining sets to a new list of dicts
        dict_generator = json_generator(tuple_header, results)
        #FIXME: empty results look confusing, return 2 lists (header,data?)
        string_stream = json.JSONEncoder(sort_keys=bool_sort_keys,iterable_as_array=True).iterencode(dict_generator)
        return string_stream

    def _format_xlsx(self, results):
        """
        Utility function, XLSX format a dataset Selection

        Keyword Parameters:
        results  -- Generator yielding a header tuple & tuples of data

        Returns:
        String generator -- formatted dataset selection

        >>> from openpyxl import load_workbook
        >>> from unittest.mock import Mock
        >>> data_source = {'id': 'my.fake', 'description': "Great data"}
        >>> fake_req = Mock()
        >>> fake_req.uri = "https://example.domain/api/v1/source/my.data/selection.xlsx"
        >>> time = datetime.now(pytz.timezone('US/Pacific'))
        >>> formatter = FormatUtil('xlsx', data_source, fake_req, time)
        >>> def test_generator1():
        ...     raise StopIteration()
        ...     yield False #impossible
        >>> out = formatter._format_xlsx(test_generator1())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> xlsx_stream = io.BytesIO(b''.join(out))#consume iterator
        >>> empty = load_workbook(xlsx_stream, read_only=True)
        >>> all(tab in empty for tab in ['data', 'description'])
        True
        >>> empty['data'].max_column, empty['data'].max_row
        (1, 1)
        >>> def test_generator2():
        ...     yield ('foo', 'bar', 'data')
        ...     yield (1, 2, 42)
        >>> out = formatter._format_xlsx(test_generator2())
        >>> '__iter__' in dir(out)#check if iterable
        True
        >>> xlsx_stream = io.BytesIO(b''.join(out))#consume iterator
        >>> two_row = load_workbook(xlsx_stream, read_only=True)
        >>> two_row['data'].max_column, two_row['data'].max_row
        (3, 2)
        >>> def test_generator3():
        ...     yield ('a', 'z', 'b')
        ...     yield (1, 26, 2)
        ...     yield (3, 28, 4)
        >>> out = formatter._format_xlsx(test_generator3())
        >>> xlsx_stream = io.BytesIO(b''.join(out))#consume iterator
        >>> three = load_workbook(xlsx_stream, read_only=True)
        >>> # check data & column order
        >>> [[cell.value for cell in row] for row in three['data'].rows]
        [['a', 'b', 'z'], [1, 2, 26], [3, 4, 28]]
        """
        bool_sort_keys=True

        # write Description tab to buffer
        write_stream = io.BytesIO()
        workbook = xlsxwriter.Workbook(write_stream)
        description_sheet = workbook.add_worksheet("description")
        cell = "A2" #first column, second row
        options = {'x_offset': 15,
                   'y_offset': 12,
                   'width': 680,
                   'height': 700}
        template = "Description:\n{}\n\nURL: {}\nRetrieved: {}"
        description = self.data_source['description']
        url = self.request.uri
        time_string = self.start_time.strftime("%B %-d, %Y %-I:%M:%S %p %Z")
        content = template.format(description, url, time_string)
        description_sheet.insert_textbox(cell, content, options)

        # write data
        data_sheet = workbook.add_worksheet("data")
        # extract the first set (header row) from the list of sets& write to sheet
        try:
            tuple_header_unsorted = next(results)
            list_header = list(tuple_header_unsorted)
            if bool_sort_keys:
                list_header.sort()
            #add header row
            header_row_index = 0 #first row
            for column_index, value in enumerate(list_header):
                data_sheet.write(header_row_index, column_index, value)
        except StopIteration: #No results! No formatting needed
            workbook.close()
            yield write_stream.getvalue()
            raise StopIteration()
        # write list of remaining sets to buffer
        try:
            worksheet_row_index = 0 #header row has already been written
            while True:
                set_row = next(results)
                worksheet_row_index += 1
                # identify how header row column may differ from data row
                for index_header, str_header in enumerate(tuple_header_unsorted):
                    # find what position this column heading has in header row
                    column_index = list_header.index(str_header)
                    cell_value = set_row[index_header]
                    data_sheet.write(worksheet_row_index, column_index, cell_value)
        except StopIteration:
            workbook.close()
            yield write_stream.getvalue()
            raise StopIteration()

    format_dicts_by_type = {
     'json': {'function': _format_json
              ,'content-type': 'application/json'}
    ,'csv' : {'function': _format_csv
              ,'content-type': 'text/csv'}
    ,'xlsx': {'function': _format_xlsx
              ,'content-type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
    }
    #Dictionary, mapping format IDs to dicts that represent format details

    @classmethod
    def get_http_content_type(cls, format_id):
        """
        Utility function, convert URI type id into HTTP Content-Type header value

        >>> FormatUtil.get_http_content_type('json')
        'application/json'
        >>> FormatUtil.get_http_content_type('Json')
        'application/json'
        >>> FormatUtil.get_http_content_type('csv')
        'text/csv'
        >>> FormatUtil.get_http_content_type('xlsx')
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        """
        lower_trimmed_id = format_id.strip().lower()
        try:
            dict_format = FormatUtil.format_dicts_by_type[lower_trimmed_id]
            http_content_type = dict_format['content-type']
            return http_content_type
        except KeyError:
            raise falcon.HTTPNotFound(description= "Unrecognized format type: "
                                                   + format_id)

def json_generator(tuple_header, row_generator):
    """
    Helper function returning the header+rows as a JSON generator
    """
    while True:
        set_row = next(row_generator)
        # build a dict; representing this rows's values, plus the header info
        dict_row = {}
        # add each element of the set to dict, using header value as key
        for index_header, str_header in enumerate(tuple_header):
            dict_row[str_header] = set_row[index_header]
        yield dict_row

def get_requested_dataset_id(sources, request, resp, params):
    """
    Get 'source_id' URL path param for selection, from a Falcon request

    Returns:
    String -- the requested ID

    Exceptions:
    falcon.HTTPNotFound -- raised when no dataset matches the falcon
      request's source_id value, source_id is not found amongst the
      falcon request's parameters, OR source_id is not available for
      selection (is_selectable==False).

    >>> import falcon.testing #Set up fake Falcon app
    >>> tb = falcon.testing.TestBase()
    >>> tb.setUp()
    >>> tr = falcon.testing.TestResource()
    >>> tb.api.add_route(tb.test_route, tr)
    >>> wsgi_iterable = tb.simulate_request(tb.test_route) #populate req
    >>> s = [{'id':'trawl.HaulCharsSat', 'name':'One Bogus Source'
    ...       ,'is_selectable': True}]
    >>> get_requested_dataset_id( s, tr.req, tr.resp, {'source_id': 'trawl.HaulCharsSat'})
    'trawl.HaulCharsSat'
    >>> s.append({'id':'trawl.HaulCharsUnSat', 'name':'A Second Source'
    ...       ,'is_selectable': False})
    >>> select2params = {'source_id': 'trawl.HaulCharsUnSat'}
    >>> get_requested_dataset_id(s, tr.req, tr.resp, select2params)
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPNotFound
    >>> get_requested_dataset_id( s, tr.req, tr.resp, {'no_id': 'SomethingElse'})
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPNotFound
    >>> get_requested_dataset_id( s, tr.req, tr.resp, {'source_id': 'FooData'})
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPNotFound
    """
    # get identifier, indicating the requested dataset
    requested_id = source_parameters.get_requested_dataset_id(sources, request
                                                              ,resp, params)
    for source in sources:
        if source['id'] == requested_id:
            if not source['is_selectable']:
                msg = "Data source not available for Selection: {}"
                raise falcon.HTTPNotFound(description=msg.format(requested_id))
            return source['id'] #Else, return the selectable ID!
    else:
        raise falcon.HTTPNotFound(description= "No data source by that name: "
                                               + requested_id)

def get_requested_format_type( params):
    """
    Extracts 'str_param_type' URL path param, from a Falcon request

    Returns:
    String -- the requested format type

    Exceptions:
    falcon.HTTPNotFound -- module's 'str_param_type' is not found amongst the
    falcon request's parameters

    >>> get_requested_format_type( {'type': 'json'})
    'json'
    >>> get_requested_format_type( {'no_type': 'SomethingElse'})
    Traceback (most recent call last):
      ...
    falcon.errors.HTTPNotFound
    """
    try:
        str_requested = params[str_param_type]
    except KeyError:
        e = falcon.HTTPNotFound(description="No selection 'format' specified in URL")
        raise e
    return str_requested
