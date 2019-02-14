"""
Module encapsulating Selection's method for Pivoting output rows

Copyright (C) 2016 ERT Inc.
"""
import ast

import pandas
import numpy

def count(collection):
    """
    module alias, to rename Python 'len' builtin for pandas aggregation
    """
    return len(collection)

def get_result(results_generator, pivot_variable_names, fact_variables):
    """
    Reformat data result rows into a wider list of Pivoted headings

    Keyword Parameters:
    results_generator  -- list generator, representing Warehouse query
      result header & data rows
    pivot_variable_names  -- list of Strings, identifying which result
      fields are to be represented as newly generated Pivot columns
      instead of simply being represented as traditional data rows with
      1x field heading.
    fact_variables  -- list of DWSupport variable objects, defining what
      aggregation method should be used on fact's Measured/Calculated
      data fields.

    >>> from pprint import pprint
    >>> variables = ['date_dim$year','product_dim$flavor','sales']
    >>> def data_generator1():
    ...     yield variables #Header row
    ...     yield ['1998', 'red', 4]
    ...     yield ['1998', 'blue', 53]
    ...     yield ['2001', 'orange', 7]
    ...     yield ['2001', 'red', 45]
    ...     yield ['2001', 'blue', 106]
    >>> columns = ['product_dim$flavor'] #Generate pivot columns,for all flavors
    >>> dwsupport_fact_variables = [{ 'column': 'sales'
    ...                              ,'python_type': 'int'}]
    >>> output_data = get_result(data_generator1(), columns, dwsupport_fact_variables)
    >>> pprint([row for row in output_data])
    [['date_dim$year',
      'sales(sum) product_dim$flavor(blue)',
      'sales(sum) product_dim$flavor(orange)',
      'sales(sum) product_dim$flavor(red)'],
     ('1998', 53.0, nan, 4.0),
     ('2001', 106.0, 7.0, 45.0)]
    >>> variables = ['product_dim$flavor', 'sales']
    >>> def data_generator2():
    ...     yield variables #Header row
    ...     yield ['red', 49]
    ...     yield ['blue', 159]
    ...     yield ['orange', 7]
    >>> columns = ['product_dim$flavor']
    >>> dwsupport_fact_variables = [{ 'column': 'sales'
    ...                              ,'python_type': 'int'}]
    >>> output_data = get_result(data_generator2(), columns
    ...                          ,dwsupport_fact_variables)
    >>> pprint([row for row in output_data])
    [['sales(sum) product_dim$flavor(blue)',
      'sales(sum) product_dim$flavor(orange)',
      'sales(sum) product_dim$flavor(red)'],
     (159, 7, 49)]
    >>> variables = ['date_dim$year','product_dim$flavor','sales','sales_person_dim$name']
    >>> def data_generator3():
    ...     yield variables #Header row
    ...     yield ['1998', 'red', 4, 'pat']
    ...     yield ['1998', 'blue', 28, 'pat']
    ...     yield ['1998', 'blue',  6, 'pat']
    ...     yield ['1998', 'blue', 53, 'tay']
    ...     yield ['2001', 'orange', 7, 'tay']
    ...     yield ['2001', 'red', 45, 'pat']
    ...     yield ['2001', 'blue', 106, 'tay']
    >>> columns = ['product_dim$flavor', 'sales_person_dim$name'] #Generate pivot columns,for flavor+salesmen
    >>> output_data = get_result(data_generator3(), columns, dwsupport_fact_variables)
    >>> pprint([row for row in output_data])
    [['date_dim$year',
      'sales(sum) product_dim$flavor(blue) sales_person_dim$name(pat)',
      'sales(sum) product_dim$flavor(blue) sales_person_dim$name(tay)',
      'sales(sum) product_dim$flavor(orange) sales_person_dim$name(tay)',
      'sales(sum) product_dim$flavor(red) sales_person_dim$name(pat)'],
     ('1998', 34.0, 53.0, nan, 4.0),
     ('2001', nan, 106.0, 7.0, 45.0)]
    """
    variable_names = next(results_generator)
    is_not_dim_or_role = lambda n: '$' not in n #assume all names with $ are: {dim_name|role_name}${field}
    data_headings = [name for name in variable_names
                     if is_not_dim_or_role(name)]
    nonpivot_variable_headings = [name for name in variable_names if name not in data_headings+pivot_variable_names]
    make = PivotMaker(pivot_variable_names, nonpivot_variable_headings
                      ,data_headings, fact_variables)
    final_results_generator = make.pivot(variable_names, results_generator)
    return final_results_generator

class PivotMaker:
    """
    Utility class, coupling pivot implementation w/ required data inputs
    """

    artificial_index_name = 'PivotMaker_default_index'
    # String, representing column added to results without pivot Index
    artificial_index_value = 'uniform_value_added_to_each_row'
    # String, representing the value default-Index column row will have

    def __init__(self, pivot_variable_names, nonpivot_variable_headings
                 ,data_headings, fact_variables):
        """
        encapsulate the four data inputs, required for pivot generation

        Keyword Parameters:
        pivot_variable_names  -- list of Strings, identifying which
          result fields are to be represented as newly generated Pivot
          columns instead of simply being represented as traditional
          data rows with 1x field heading.
        nonpivot_variable_names  -- list of Strings, identifying
          additional dimensional result fields on which no pivot is to
          be performed.
        data_headings  -- list of Strings, identifying fact data
          variables. Fact data is grouped/aggregated based on the pivot
          field values the fact data is related to.
        fact_variables  -- list of DWSupport variable objects, defining
          what aggregation method should be used on fact's
          Measured/Calculated data fields.
        """
        self.pivot_variable_names = pivot_variable_names
        self.nonpivot_variable_headings = nonpivot_variable_headings
        self.data_headings = data_headings
        self.fact_variables = fact_variables

    def pivot(self, input_header_row, data_rows_generator):
        """
        Return tuple generator, encapsulating the pivot creation process

        Keyword Parameters:
        input_header_row  -- list of strings, representing Warehouse
          result headings
        data_rows_generator  -- list generator, representing Warehouse
          data result
        """
        df = pandas.DataFrame(data_rows_generator, columns=input_header_row)

        # if data is ALL pivot variables & data variables
        if self._artificial_index_needed():
            df[self.artificial_index_name] = self.artificial_index_value
            self.nonpivot_variable_headings.append(self.artificial_index_name)
        #http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.pivot_table.html#pandas.DataFrame.pivot_table
        pivot_args = {
            'index': self.nonpivot_variable_headings
            ,'columns': self.pivot_variable_names
            ,'values': self.data_headings
            ,'aggfunc': [numpy.sum, count]
        }
        pivot_results = pandas.DataFrame.pivot_table(df, **pivot_args)
        # pivot_table generates Pivot columns for 'values' using every
        # 'aggfunc' - most of these combinations we don't really want.
        self._drop_extra_columns(pivot_results)
        pivot_index_rows = pivot_results.iterrows()

        # get Header names - but remove default index column (if unneeded)
        keep_pivot_index = True
        if self._artificial_index_needed():
            keep_pivot_index = False
        pivot_datatypes = pivot_results.to_records(keep_pivot_index).dtype
        pivot_header_names = pivot_datatypes.names
        #convert Pandas output,back to Warehouse format (list of lists w/ header row)
        reformatted_pivot_header = []
        for h in pivot_header_names:
            if self._is_pivot_column(h):
                #Assume Pandas is using our pivot fields, in order:
                new_name = self._format_header(h)
                reformatted_pivot_header.append(new_name)
                continue
            #else - no changes needed, simply append
            reformatted_pivot_header.append(h)
        # generate results
        yield reformatted_pivot_header
        while True:
            #FIXME:this conversion returns nan, not None
            default_index_column_value, row = next(pivot_index_rows)
            row_tuple = tuple(row)
            output = (default_index_column_value,) + row_tuple
            # remove default index column (if one was added)
            if self._artificial_index_needed():
                output = row_tuple #no index column
            yield output

    def _is_pivot_column(self, field_name):
        """
        Check if field_name value could *never* be a pivot heading

        Keyword Parameters:
        field_name  -- String, representing a possible Pandas pivot
          column heading

        >>> pivots = ['person_dim$bob']
        >>> nonpivots = []
        >>> data = ['samples_cnt']
        >>> fact_vars = [{'column': 'samples_cnt','python_type': 'int'}]
        >>> test = PivotMaker(pivots, nonpivots, data, fact_vars)
        >>> a_pivot_heading = 'sum person_dim$bob(newhart) samples_cnt'
        >>> test._is_pivot_column(a_pivot_heading)
        True
        >>> not_a_pivot_heading = 'samples_cnt'
        >>> test._is_pivot_column(not_a_pivot_heading)
        False
        >>> test._is_pivot_column('foo_anything_unrecognized')
        True
        """
        never_a_pivot_column = self.data_headings + self.nonpivot_variable_headings
        is_pivot = field_name not in never_a_pivot_column
        return is_pivot

    def _artificial_index_needed(self):
        """
        True if pivot would yeild column heading with no Data field name

        Pandas heirarchical column headings for pivots take the form:
        ('aggfunc_name', 'data_var_name', 'pivot_var1_value', [ ... 'pivot_varN_value'])

        If no fields are specified as an pivot_table 'index' parameter
        Pandas will instead create a DataFrame index, populate it with
        the names of the data vars, and yeild a (more difficult to use)
        set of results with heirarchical headings of form:
        ('aggfunc_name', 'pivot_var1_value', [ ... 'pivot_varN_value'])

        >>> nonpivots = ['year']
        >>> test = PivotMaker([], nonpivots, [], [])
        >>> test._artificial_index_needed()
        False
        >>> nonpivots = []
        >>> test = PivotMaker([], nonpivots, [], [])
        >>> test._artificial_index_needed()
        True
        """
        nonpivots = set(self.nonpivot_variable_headings) - set([self.artificial_index_name])
        if nonpivots:
            return False
        return True

    def _drop_extra_columns(self, data_frame):
        """
        Remove (in-place) generated DataFrame.pivot columns we dont need

        Columns are generated for every possible combination of data
        variable and pivot 'aggfunc' parameter. We only need the data
        variable & 'aggfunc' combinations listed in
        PivotMaker.fact_variables

        Keyword Parameters:
        data_frame  -- Pandas DataFrame representing a unmodified
          'pivot' of the PivotMaker.pivot() data_results parameter.

        >>> pivots = ['flavor']
        >>> nonpivots = ['name']
        >>> data = ['sales', 'day']
        >>> missing_factvars = []
        >>> test = PivotMaker(pivots, nonpivots, data, missing_factvars)
        >>> data_variable_names = ['sales', 'day']
        >>> #Fake some pivot output
        >>> df = pandas.DataFrame([ ['a',2,2,'Monday','SundaySunday',1,1,1,9]
        ...                        ,['b',3,3,'SundaySunday','Wednesday',4,4,2,1]]
        ...                       ,columns=[ 'name'
        ...                                 ,('sum', 'sales', 'blue')
        ...                                 ,('sum', 'sales', 'red')
        ...                                 ,('sum', 'day', 'blue')
        ...                                 ,('sum', 'day', 'red')
        ...                                 ,('count', 'sales', 'blue')
        ...                                 ,('count', 'sales', 'red')
        ...                                 ,('count', 'day', 'blue')
        ...                                 ,('count', 'day', 'red')])
        >>> test._drop_extra_columns(df)
        Traceback (most recent call last):
          ...
        Exception: "sales" not found in fact_variables: []
        >>> fact_vars = [{'column': 'sales','python_type': 'int'}
        ...              ,{'column': 'day','python_type': 'str'}]
        >>> test = PivotMaker(pivots, nonpivots, data, fact_vars)
        >>> test._drop_extra_columns(df)
        >>> df
          name  (sum, sales, blue)  (sum, sales, red)  (count, day, blue)  \\
        0    a                   2                  2                   1   
        1    b                   3                  3                   2   
        <BLANKLINE>
           (count, day, red)  
        0                  9  
        1                  1  
        """
        #remove pivot columns that are not on our type->aggregate mapping
        type_aggregate = {'str': 'count'
                          ,'datetime.datetime': 'count'
                          ,'int': 'sum'
                          ,'float': 'sum'
                         } # dictionary of aggregates we *do* want, by field type
        column_type = {} # build a dictionary of types by data column name
        for variable in self.fact_variables:
            column, constructor = variable['column'], variable['python_type']
            column_type[column] = constructor
        # remove the unneeded pivot columns
        for key in data_frame:
            if self._is_pivot_column(key):
                aggregation_method, data_variable_name = key[:2]
                # find aggregate we want to use, for this data field
                try:
                    data_variable_type = column_type[data_variable_name]
                except KeyError as e:
                    msg = ('"{}" not found in fact_variables: {}'
                           .format(data_variable_name,self.fact_variables) )
                    raise Exception(msg)#TODO: make this a custom module class
                target_method = type_aggregate[data_variable_type]
                if not aggregation_method == target_method:
                    del data_frame[key] #no match: remove pivot column

    def _format_header(self, pandas_pivot_header):
        """
        Turn Pandas' autogenerated Pivot column headings into our convention

        Keyword Parameters:
        pandas_pivot_header  -- String, represented a Pandas pivot column
          heading.

        >>> pivot_variables = ['flavor']
        >>> test = PivotMaker(pivot_variables, [], [], [])
        >>> test._format_header("('sum', 'sales', 'blue')")
        'sales(sum) flavor(blue)'
        >>> pivot_variables = ['flavor', 'person']
        >>> test = PivotMaker(pivot_variables, [], [], [])
        >>> test._format_header("('count', 'sales', 'blue', 'pat')")
        'sales(count) flavor(blue) person(pat)'
        """
        parse_tuple = self._parse_heading(pandas_pivot_header)
        aggregation_method, data_variable_name, pivot_variable_values = parse_tuple
        # and format...
        prefix = data_variable_name+'({})'.format(aggregation_method)
        field_template = ' {pivot_variable}({pivot_value})'
        for index,field in enumerate(self.pivot_variable_names):
            value = pivot_variable_values[index]
            prefix = prefix+field_template.format(pivot_variable=field
                                                  ,pivot_value=value)
        return prefix

    def _parse_heading(self, pandas_pivot_header):
        """
        Returns names of pivot_table aggfunc&value field,+pivot ordered list

        The pivot ordered list consists of a unique data item value from
        each of the pivot fields (e.g.: ['pat', 'Friday'] for pivot columns
         ['name','day'])

        Keyword Parameters:
        pandas_pivot_header  -- String representing a 'pivot_table'
          heirarchal column heading.

        >>> test = PivotMaker([],[],[],[])
        >>> test._parse_heading("('sum', 'sales', 'blue')")
        ('sum', 'sales', ('blue',))
        >>> test._parse_heading("('count', 'sales', 'blue', 'pat')")
        ('count', 'sales', ('blue', 'pat'))
        """
        # safely parse the Pandas string
        #https://docs.python.org/dev/library/ast.html#ast.literal_eval
        pandas_header_tuple = ast.literal_eval(pandas_pivot_header)
        aggregation_method = pandas_header_tuple[0]
        data_variable_name = pandas_header_tuple[1]
        pivot_variable_values = pandas_header_tuple[2:]
        return aggregation_method, data_variable_name, pivot_variable_values
