"""
Module encapsulating FRAM Data Warehouse OLAP sql generation methods

Copyright (C) 2016 ERT Inc.
"""
import sqlalchemy as sql
import sqlalchemy.dialects.postgresql as postgresql

from api.resources.source.warehouse import util
from api.resources.source.selection import parameters
from api import json

class FieldOlapRole(Exception):
    """
    _get_sql_field_name evoked on an Alias Column
    """
    pass

class ExceptionFactSQLAlchemyTable(Exception): #FIXME:normal program logic should not be implemented with exceptions!
    """
    _get_sqlalchemy_table_plus_mapped_columns has completed a Table for fact_name
    """
    def __init__(self, fact_table):
        Exception.__init__(self)
        self.table = fact_table

def get_fact_sql(fact_name, schema, variables_by_table_name
                 ,associations_by_parent, aliases, model, nonselect_tables
                 ,filters, empty_cell_dimensions = []):
    """
    Returns string SQL+SQLAlchemy binds,for filtered fact+dim field data

    Keyword Parameters:
    fact_name  -- String representation of the fact table name
    schema  --  String, representing db schema location of all tables
    variables_by_table_name  --  Dict, representing lists of 'variable'
      warehouse support Data Transfer Objects mapped to their table name.
    association_by_parent  --  Dict of warehouse support 'association' DTOs by
      parent table_name.
    aliases  -- list of Strings, representing the names of tables which
      are actually dimensional Roles (dimension aliases).
    model  -- dictionary of lists, representing warehouse configuration
      model.
    nonselect_tables  -- list of Strings, representing the names of
      tables which are only included to support dimensional Roles & are
      not to be included in the generated SQL output
    filters  -- list of Strings, representing Selection filter expressions
    empty_cell_dimensions  -- list of Strings representing Dimension
       tables (or OLAP-Roles) which are to be OUTER JOINED to produce
       empty Fact value cells for all Dimensional values not found in
       the fact.

    >>> from copy import deepcopy
    >>> dim_attr1 = { 'id': 1, 'column':'bar_ml', 'title':'bar'\
                ,'python_type': 'float' \
                ,'table': 'foo_dim'}
    >>> dim_attr2 = { 'id': 2, 'column':'baz_kg', 'title':'baz'\
                ,'python_type': 'float' \
                ,'table': 'foo_dim'}
    >>> fact_attr1 = { 'id': 1, 'column':'frob_measure_sec', 'title':'frob'\
                ,'python_type': 'float' \
                ,'table': 'foo_fact'}
    >>> fact_attr2 = { 'id': 2, 'column':'bar_ml','title':'bar (foo observed)'\
                ,'python_type': 'float' \
                ,'table': 'foo_fact'}
    >>> vars_by_tab = { 'foo_dim':[dim_attr1, dim_attr2] \
                       ,'foo_fact':[fact_attr1, fact_attr2]}
    >>> assoc1 = {'type':'fact dimension','table':'foo_fact','column':'foo_dim_id'\
                 ,'parent': 'foo_dim','parent_column': 'foo_dim_id' }
    >>> no_roles = []
    >>> assoc_by_dim = {'foo_dim': assoc1 }
    >>> no_nonselects = []
    >>> filters = []
    >>> model_no_custom_ids = {'variable_custom_identifiers': []}
    >>> sql, binds = get_fact_sql('foo_fact', 'proj1', vars_by_tab
    ...                           ,assoc_by_dim, no_roles, model_no_custom_ids, no_nonselects
    ...                           ,filters)
    >>> sql
    'SELECT proj1.foo_dim.bar_ml AS foo_dim$bar_ml, proj1.foo_dim.baz_kg AS foo_dim$baz_kg, proj1.foo_fact.frob_measure_sec, proj1.foo_fact.bar_ml \\nFROM proj1.foo_fact JOIN proj1.foo_dim ON proj1.foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id'
    >>> binds
    {}
    >>> assoc_role = { 'type':'fact dimension role', 'table':'foo_fact'
    ...               ,'column':'foo_dim_id', 'parent': 'foo_dim'
    ...               ,'parent_column': 'foo_dim_id' }
    >>> assoc_base = { 'type':'dimension role base'
    ...               ,'table':'another_foo_dim', 'column':'foo_dim_id'
    ...               ,'parent': 'foo_dim'
    ...               ,'parent_column': 'foo_dim_id' }
    >>> role = 'another_foo_dim'
    >>> vars_by_tab_with_role = deepcopy(vars_by_tab)
    >>> role_attr1, role_attr2 = dict(dim_attr1), dict(dim_attr2)
    >>> role_attr1['table'] = 'another_foo_dim'
    >>> role_attr2['table'] = 'another_foo_dim'
    >>> vars_by_tab_with_role[ role] = [role_attr1, role_attr2]
    >>> assoc_by_dim = { 'foo_dim': assoc1
    ...                 , role: assoc_role}
    >>> role_names = [ role]
    >>> sql, binds = get_fact_sql('foo_fact', 'proj1', vars_by_tab_with_role
    ...                           ,assoc_by_dim, role_names, model_no_custom_ids, no_nonselects
    ...                           ,filters)
    >>> sql
    'SELECT proj1.foo_dim.bar_ml AS foo_dim$bar_ml, proj1.foo_dim.baz_kg AS foo_dim$baz_kg, proj1.foo_fact.frob_measure_sec, proj1.foo_fact.bar_ml, another_foo_dim.bar_ml AS another_foo_dim$bar_ml, another_foo_dim.baz_kg AS another_foo_dim$baz_kg \\nFROM proj1.foo_fact JOIN proj1.foo_dim ON proj1.foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id JOIN proj1.foo_dim AS another_foo_dim ON another_foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id'
    >>> binds
    {}
    >>> nonselects = ['foo_dim']
    >>> sql, binds = get_fact_sql('foo_fact', 'proj1', vars_by_tab_with_role
    ...                           ,assoc_by_dim, role_names, model_no_custom_ids, nonselects
    ...                           ,filters)
    >>> sql
    'SELECT proj1.foo_fact.frob_measure_sec, proj1.foo_fact.bar_ml, another_foo_dim.bar_ml AS another_foo_dim$bar_ml, another_foo_dim.baz_kg AS another_foo_dim$baz_kg \\nFROM proj1.foo_fact JOIN proj1.foo_dim ON proj1.foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id JOIN proj1.foo_dim AS another_foo_dim ON another_foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id'
    >>> binds
    {}
    >>> filters = ['another_foo_dim$bar_ml>=99']
    >>> sql, binds = get_fact_sql('foo_fact', 'proj1', vars_by_tab_with_role
    ...                           ,assoc_by_dim, role_names, model_no_custom_ids, nonselects
    ...                           ,filters)
    >>> sql
    'SELECT proj1.foo_fact.frob_measure_sec, proj1.foo_fact.bar_ml, another_foo_dim.bar_ml AS another_foo_dim$bar_ml, another_foo_dim.baz_kg AS another_foo_dim$baz_kg \\nFROM proj1.foo_fact JOIN proj1.foo_dim ON proj1.foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id JOIN proj1.foo_dim AS another_foo_dim ON another_foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id AND another_foo_dim.bar_ml >= %(0)s'
    >>> binds
    {'0': 99.0}
    >>> model_custom_ids = {'variable_custom_identifiers': [
    ...                         { 'table': 'another_foo_dim'
    ...                          ,'column': 'baz_kg'
    ...                          ,'id': 'baz'}]}
    >>> sql, binds = get_fact_sql('foo_fact', 'proj1', vars_by_tab_with_role
    ...                           ,assoc_by_dim, role_names, model_custom_ids, nonselects
    ...                           ,filters)
    >>> sql
    'SELECT proj1.foo_fact.frob_measure_sec, proj1.foo_fact.bar_ml, another_foo_dim.bar_ml AS another_foo_dim$bar_ml, another_foo_dim.baz_kg AS baz \\nFROM proj1.foo_fact JOIN proj1.foo_dim ON proj1.foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id JOIN proj1.foo_dim AS another_foo_dim ON another_foo_dim.foo_dim_id = proj1.foo_fact.foo_dim_id AND another_foo_dim.bar_ml >= %(0)s'
    >>> binds
    {'0': 99.0}
    """
    #compose SQL column definitions, for the facts+nonRole dimensions
    init_cols = _get_unattached_columns( fact_name
                                           ,variables_by_table_name
                                           ,aliases
                                           ,model
    )
    columns_unlabeled, columns_by_table_name = init_cols

    #make SQL tables, map SQLcolumn defs to tables+label them, add Role columns
    fact_cols_dims_tuple = _get_attached_fact_cols_dims_tuple(
         fact_name
        ,schema
        ,columns_unlabeled
        ,columns_by_table_name
        ,variables_by_table_name
        ,associations_by_parent
        ,aliases
        ,model
    )
    fact_table, columns_plus_table_info_and_role_cols, dim_relation_tuples = (
        fact_cols_dims_tuple
    )

    #compose the joins
    python_types, variables_and_tables_by_web_name = (
        _get_types_and_variable_table_pairs(fact_name, variables_by_table_name, model)
    )
    json_python_types = json.dumps(python_types)
    statement, binds = _get_sqlalchemy_statement_filtered(
         fact_table
        ,columns_plus_table_info_and_role_cols
        ,dim_relation_tuples
        ,nonselect_tables
        ,json_python_types
        ,filters
        ,variables_and_tables_by_web_name
        ,empty_cell_dimensions
    )

    postgresql_statement = statement.compile(dialect=postgresql.dialect())
    string_sql = str(postgresql_statement)
    return string_sql, binds

def _get_types_and_variable_table_pairs(fact_name, variables_by_table_name, model):
    """
    returns dicts of variable types & variable+table name pairs

    Keyword Parameters:
    fact_name  -- String, representing the name of the fact table OLAP
      cube SQL is being generated for.
    variables_by_table_name  -- Dict representing lists of DWSupport
      variables, indexed by the variables DWSupport table name (name may
      be a Role)
    model  -- dictionary of lists, representing warehouse configuration
      model.

    >>> from pprint import pprint
    >>> fact = 'great_fact'
    >>> dim_attr1 = { 'id': 1, 'column':'bar_ml', 'title':'bar'
    ...              ,'python_type': 'float'
    ...              ,'table': 'foo_dim'}
    >>> dim_attr2 = { 'id': 2, 'column':'baz_kg', 'title':'baz'
    ...              ,'python_type': 'float'
    ...              ,'table': 'foo_dim'}
    >>> fact_attr1 = { 'id': 1, 'column':'frob_measure_sec'
    ...               ,'title':'frob', 'python_type': 'float'
    ...               ,'table': 'great_fact'}
    >>> fact_attr2 = { 'id': 2, 'column':'bar_ml'
    ...               ,'title':'bar (foo observed)'
    ...               ,'python_type': 'float', 'table': 'great_fact'}
    >>> vars_by_tab = { 'foo_dim':[dim_attr1, dim_attr2]
    ...                ,'great_fact':[fact_attr1, fact_attr2]}
    >>> model_no_custom_ids = {'variable_custom_identifiers': []}
    >>> variables, variable_table_pairs = (
    ...     _get_types_and_variable_table_pairs(fact,vars_by_tab,model_no_custom_ids))
    >>> pprint(variables)
    {'bar_ml': 'float',
     'foo_dim$bar_ml': 'float',
     'foo_dim$baz_kg': 'float',
     'frob_measure_sec': 'float'}
    >>> pprint(variable_table_pairs)
    {'bar_ml': ({'column': 'bar_ml',
                 'id': 2,
                 'python_type': 'float',
                 'table': 'great_fact',
                 'title': 'bar (foo observed)'},
                'great_fact'),
     'foo_dim$bar_ml': ({'column': 'bar_ml',
                         'id': 1,
                         'python_type': 'float',
                         'table': 'foo_dim',
                         'title': 'bar'},
                        'foo_dim'),
     'foo_dim$baz_kg': ({'column': 'baz_kg',
                         'id': 2,
                         'python_type': 'float',
                         'table': 'foo_dim',
                         'title': 'baz'},
                        'foo_dim'),
     'frob_measure_sec': ({'column': 'frob_measure_sec',
                           'id': 1,
                           'python_type': 'float',
                           'table': 'great_fact',
                           'title': 'frob'},
                          'great_fact')}
    >>> model_custom_ids = {'variable_custom_identifiers': [
    ...                         { 'table': 'foo_dim'
    ...                          ,'column': 'baz_kg'
    ...                          ,'id': 'baz'}]}
    >>> variables, variable_table_pairs = (
    ...     _get_types_and_variable_table_pairs(fact,vars_by_tab, model_custom_ids))
    >>> pprint(variables)
    {'bar_ml': 'float',
     'baz': 'float',
     'foo_dim$bar_ml': 'float',
     'frob_measure_sec': 'float'}
    >>> pprint(variable_table_pairs)
    {'bar_ml': ({'column': 'bar_ml',
                 'id': 2,
                 'python_type': 'float',
                 'table': 'great_fact',
                 'title': 'bar (foo observed)'},
                'great_fact'),
     'baz': ({'column': 'baz_kg',
              'id': 2,
              'python_type': 'float',
              'table': 'foo_dim',
              'title': 'baz'},
             'foo_dim'),
     'foo_dim$bar_ml': ({'column': 'bar_ml',
                         'id': 1,
                         'python_type': 'float',
                         'table': 'foo_dim',
                         'title': 'bar'},
                        'foo_dim'),
     'frob_measure_sec': ({'column': 'frob_measure_sec',
                           'id': 1,
                           'python_type': 'float',
                           'table': 'great_fact',
                           'title': 'frob'},
                          'great_fact')}
    """
    python_types = {} #build map of Python types, by Web name
    variable_table_pairs_by_web_name = {} #build Bonus map,of var+Table names
    for table_name in variables_by_table_name:
        for var in variables_by_table_name[table_name]:
            web_name = util.prefix_field_name(var['column'], table_name)
            if table_name == fact_name:
                web_name = var['column']
            # override the variable ID, if DWSupport specifies a custom ID
            custom_web_name = util.get_custom_variable_name(var, model)
            if custom_web_name is not None:
                web_name = custom_web_name
            python_types[web_name] = var['python_type']
            variable_table_pairs_by_web_name[web_name] = (var,table_name)
    return python_types, variable_table_pairs_by_web_name


def _get_sqlalchemy_statement_filtered(fact_table, columns
                                       ,dimension_association_tuples
                                       ,nonselect_tables, json_python_types
                                       ,filters
                                       ,variables_and_tables_by_web_name
                                       ,empty_cell_dimensions = []):
    """
    Construct SQL statement+bind dict from SQLAlchemy+DWSupport objects

    Keyword Parameters:
    fact_table  -- SQLAlchemy Table representing a Warehouse fact table
    columns  -- list of SQLAlchemy Columns belonging to fact_table & all
      associated Dimension tables or OLAP-Roles.
    dimension_association_tuples  -- list of SQLAlchemy Table &
      DWSupport association pairs, representing Dimension tables (or
      OLAP-Roles) & their corresponding DW logical relationships.
    nonselect_tables  -- list of Strings, representing the names of
      tables which are only included to support dimensional Roles & are
      not to be included in the generated SQL output
    json_python_types  -- JSON encoded string representing a Dict that
      maps field names to Python type constructors
    filters  -- list of Strings, representing Selection filter
      expressions
    variables_and_tables_by_web_name -- Dict representing pairs of
       DWSupport variables + variable's source table/role alias name,
       indexed by the Web name that API users would refer to var by.
    empty_cell_dimensions  -- list of Strings representing Dimension
       tables (or OLAP-Roles) which are to be OUTER JOINED to produce
       empty Fact value cells for all Dimensional values not found in
       the fact.

    >>> table = 'date_dim'
    >>> fact_name = 'test_fact'
    >>> schema = 'foo'
    >>> init_cols = [sql.Column('test_measure_kg')] #Test fact select
    >>> cols_by_table = {'test_fact':init_cols}
    >>> var_by_table = {'test_fact':[ {'python_type': 'float'
    ...                                 ,'table': 'test_fact', 'id': 3
    ...                                 ,'title': 'test_measure_kg'
    ...                                 ,'column': 'test_measure_kg'}] }
    >>> assoc_by_parent = {}
    >>> aliases = [] #no OLAP-Roles
    >>> model_no_custom_ids = {'variable_custom_identifiers': []}
    >>> fact, cols, assocs = _get_attached_fact_cols_dims_tuple(fact_name, schema, init_cols, cols_by_table, var_by_table, assoc_by_parent, aliases, model_no_custom_ids)
    >>> nonselect, filters = [], []
    >>> python_types_garbage, variable_table_pairs = (
    ...     _get_types_and_variable_table_pairs(fact_name, var_by_table, model_no_custom_ids))
    >>> types = '{"month_name": "str", "year": "int", "test_measure_kg": "float"}'
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs)
    >>> str(statement)
    'SELECT foo.test_fact.test_measure_kg \\nFROM foo.test_fact'
    >>> binds
    {}
    >>> filters = ['test_measure_kg>=100']
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs)
    >>> str(statement)
    'SELECT foo.test_fact.test_measure_kg \\nFROM foo.test_fact \\nWHERE test_fact.test_measure_kg >= :0'
    >>> binds
    {'0': 100.0}
    >>> init_cols = [sql.Column('month_name'), sql.Column('year'), sql.Column('test_measure_kg')]
    >>> cols_by_table = {'date_dim':init_cols[0:2],'test_fact':[init_cols[2]]}
    >>> var_by_table = {'date_dim':[ {'python_type': 'str', 'table': 'date_dim'
    ...                               ,'id': 1, 'title': 'month_name'
    ...                               ,'column': 'month_name'}
    ...                             ,{'python_type': 'int', 'table': 'date_dim'
    ...                               ,'id': 2, 'title': 'year'
    ...                               ,'column': 'year'}]
    ...                 ,'test_fact':[ {'python_type': 'float'
    ...                                 ,'table': 'test_fact', 'id': 3
    ...                                 ,'title': 'test_measure_kg'
    ...                                 ,'column': 'test_measure_kg'}] }
    >>> assoc_by_parent = {'date_dim': { 'type': 'fact dimension'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'} }
    >>> filters = []
    >>> fact, cols, assocs = _get_attached_fact_cols_dims_tuple(fact_name, schema, init_cols, cols_by_table, var_by_table, assoc_by_parent, aliases, model_no_custom_ids)
    >>> python_types_garbage, variable_table_pairs = (
    ...     _get_types_and_variable_table_pairs(fact_name, var_by_table, model_no_custom_ids))
    >>> types = '{"month_name": "str", "year": "int", "test_measure_kg": "float"}'
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs)
    >>> str(statement)
    'SELECT foo.date_dim.month_name, foo.date_dim.year, foo.test_fact.test_measure_kg \\nFROM foo.test_fact JOIN foo.date_dim ON foo.date_dim.date_whid = foo.test_fact.date_whid'
    >>> binds
    {}
    >>> #Test again, with an OLAP-Role
    >>> init_cols = [sql.Column('month_name'), sql.Column('year'), sql.Column('test_measure_kg')]
    >>> cols_by_table = {'date_dim':init_cols[0:2],'test_fact':[init_cols[2]]}
    >>> var_by_table['special_date_dim'] = [ {'python_type': 'str'
    ...                                       ,'table': 'special_date_dim'
    ...                                       ,'id': 1, 'title': 'month_name'
    ...                                       ,'column': 'month_name'}
    ...                                      ,{'python_type': 'int'
    ...                                       ,'table': 'special_date_dim'
    ...                                       ,'id': 2, 'title': 'year'
    ...                                       ,'column': 'year'}]
    >>> assoc_by_parent = {'date_dim': { 'type': 'fact dimension'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'}
    ...                   ,'special_date_dim': { 'type': 'fact dimension role'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'special_date_whid'
    ...                                 ,'parent_column': 'date_whid'} }
    >>> aliases = ['special_date_dim']
    >>> fact, cols, assocs = _get_attached_fact_cols_dims_tuple(fact_name, schema, init_cols, cols_by_table, var_by_table, assoc_by_parent, aliases, model_no_custom_ids)
    >>> nonselect = [] #include date_dim + special_date_dim (Role) fields
    >>> python_types_garbage, variable_table_pairs = (
    ...     _get_types_and_variable_table_pairs(fact_name, var_by_table, model_no_custom_ids))
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs)
    >>> str(statement)
    'SELECT foo.date_dim.month_name, foo.date_dim.year, foo.test_fact.test_measure_kg, special_date_dim.month_name AS special_date_dim$month_name, special_date_dim.year AS special_date_dim$year \\nFROM foo.test_fact JOIN foo.date_dim ON foo.date_dim.date_whid = foo.test_fact.date_whid JOIN foo.date_dim AS special_date_dim ON special_date_dim.date_whid = foo.test_fact.special_date_whid'
    >>> binds
    {}
    >>> #Test a third time, with a standalone OLAP-Role
    >>> init_cols = [sql.Column('month_name'), sql.Column('year'), sql.Column('test_measure_kg')]
    >>> cols_by_table = {'date_dim':init_cols[0:2],'test_fact':[init_cols[2]]}
    >>> fact, cols, assocs = _get_attached_fact_cols_dims_tuple(fact_name, schema, init_cols, cols_by_table, var_by_table, assoc_by_parent, aliases, model_no_custom_ids)
    >>> nonselect = ['date_dim']
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs)
    >>> str(statement)
    'SELECT foo.test_fact.test_measure_kg, special_date_dim.month_name AS special_date_dim$month_name, special_date_dim.year AS special_date_dim$year \\nFROM foo.test_fact JOIN foo.date_dim ON foo.date_dim.date_whid = foo.test_fact.date_whid JOIN foo.date_dim AS special_date_dim ON special_date_dim.date_whid = foo.test_fact.special_date_whid'
    >>> binds
    {}
    >>> #Test with a customized Variable field name
    >>> init_cols = [sql.Column('month_name'), sql.Column('year'), sql.Column('test_measure_kg')]
    >>> cols_by_table = {'date_dim':init_cols[0:2],'test_fact':[init_cols[2]]}
    >>> fact, cols, assocs = _get_attached_fact_cols_dims_tuple(fact_name, schema, init_cols, cols_by_table, var_by_table, assoc_by_parent, aliases, model_no_custom_ids)
    >>> nonselect = ['date_dim']
    >>> model_custom_ids = {'variable_custom_identifiers': []} #TODO: define
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs)
    >>> str(statement)
    'SELECT foo.test_fact.test_measure_kg, special_date_dim.month_name AS special_date_dim$month_name, special_date_dim.year AS special_date_dim$year \\nFROM foo.test_fact JOIN foo.date_dim ON foo.date_dim.date_whid = foo.test_fact.date_whid JOIN foo.date_dim AS special_date_dim ON special_date_dim.date_whid = foo.test_fact.special_date_whid'
    >>> binds
    {}
    >>> filters = ['test_measure_kg<40'] #Test filter SQL for a fact column
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs)
    >>> str(statement)
    'SELECT foo.test_fact.test_measure_kg, special_date_dim.month_name AS special_date_dim$month_name, special_date_dim.year AS special_date_dim$year \\nFROM foo.test_fact JOIN foo.date_dim ON foo.date_dim.date_whid = foo.test_fact.date_whid AND test_fact.test_measure_kg < :0 JOIN foo.date_dim AS special_date_dim ON special_date_dim.date_whid = foo.test_fact.special_date_whid'
    >>> binds
    {'0': 40.0}
    >>> empties = ['special_date_dim'] #Test an EMPTY cells dimension
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs, empties)
    >>> str(statement)
    'SELECT foo.test_fact.test_measure_kg, special_date_dim.month_name AS special_date_dim$month_name, special_date_dim.year AS special_date_dim$year \\nFROM foo.date_dim AS special_date_dim LEFT OUTER JOIN (foo.test_fact JOIN foo.date_dim ON foo.date_dim.date_whid = foo.test_fact.date_whid AND test_fact.test_measure_kg < :0) ON special_date_dim.date_whid = foo.test_fact.special_date_whid'
    >>> binds
    {'0': 40.0}
    >>> empties = ['special_date_dim','date_dim'] #Test 2x EMPTY cells dimension
    >>> statement, binds = _get_sqlalchemy_statement_filtered(
    ...     fact, cols, assocs, nonselect, types, filters, variable_table_pairs, empties)
    >>> str(statement)
    'SELECT foo.test_fact.test_measure_kg, special_date_dim.month_name AS special_date_dim$month_name, special_date_dim.year AS special_date_dim$year \\nFROM foo.date_dim AS special_date_dim FULL OUTER JOIN (foo.date_dim LEFT OUTER JOIN foo.test_fact ON foo.date_dim.date_whid = foo.test_fact.date_whid AND test_fact.test_measure_kg < :0) ON special_date_dim.date_whid = foo.test_fact.special_date_whid'
    >>> binds
    {'0': 40.0}
    """
    #prepare filtering access conditions
    fact_filters = []
    # list of filtering expressions for the Fact table
    fact_filters_unprocessed, one_empty_cell_dim_joined = True, False
    #flag, to track when filters are added
    #and a flag to track when an EMPTY cell dim added
    filters_by_table = {}
    # dict of filter expressions
    for filter_urlencoded in filters:
        web_field = parameters.get_filter_processed_3tuple(json_python_types, filter_urlencoded)[0]
        var, table_name = variables_and_tables_by_web_name[web_field]
        if table_name == fact_table.name:
            fact_filters.append(filter_urlencoded)
            continue
        filters = filters_by_table.get(table_name, [])#new list, if not found
        filters.append(filter_urlencoded)
        filters_by_table[table_name] = filters

    # build the joins, starting with the fact table
    join_clause = fact_table
    binds = {}
    # dimension EMPTY cell requests are 1) done last, 2) RIGHT OUTER joined
    empty_cells = [t for t in dimension_association_tuples if t[0].name in empty_cell_dimensions]
    suppress_empty_cells = [t for t in dimension_association_tuples if t not in empty_cells]
    for dimension, parent_association in suppress_empty_cells+empty_cells:
        # retrieve SQLAlchemy Column obj,for both sides of the JOIN conditional
        dim_field_name, fact_field_name = (parent_association['parent_column']
                                           ,parent_association['column'] )
        dim_column, fact_column = (dimension.c[dim_field_name]
                                   ,fact_table.c[fact_field_name])
        # join on the dimension table
        right = dimension#style preference:(inner)join dimension,onto the right
        onclause = (dim_column == fact_column)
        # if specified, add additional filtering onclauses & binds
        try:
            dimension_filters = filters_by_table[dimension.name]
        except KeyError:
            dimension_filters = []
        if fact_filters_unprocessed:
            dimension_filters = fact_filters + dimension_filters
            fact_filters_unprocessed = False #now, they've been processed!
        for filter_urlencoded in dimension_filters:
            start_bind = len(binds)
            filter_tuple = parameters.get_filter_condition_sqlalchemy_pgsql_string(
                json_python_types
                ,filter_urlencoded
                ,start_bind)
            filter_expression, filter_binds = filter_tuple
            # replace web 'table$field' name with join 'schema.table.column'
            web_field = parameters.get_filter_processed_3tuple(json_python_types, filter_urlencoded)[0]
            var, table_name = variables_and_tables_by_web_name[web_field]
            join_column = '.'.join([table_name, var['column']])
            rewritten_expression = filter_expression.lstrip().replace(web_field,join_column)
            binds.update(filter_binds)
            sa_text = sql.text(rewritten_expression)
            onclause = onclause & sa_text#append condition
        if dimension.name in empty_cell_dimensions:
            # RIGHT OUTER JOIN the 1st Dim we're adding EMPTY cells for
            join_clause = right.join(join_clause, onclause, isouter=True
                                     ,full=one_empty_cell_dim_joined)
            one_empty_cell_dim_joined= True#FULL OUTER JOIN,all additional dims
            continue
        #else, default to a regular join (suppress EMPTY dimensional values)
        join_clause = join_clause.join(right, onclause)
    # select only the dimension columns which are actually referenced on fact
    select_columns = []
    for c in columns:
        # add to select list, if from OLAP role or table not on nonselect list
        if _is_olap_role( c):
            select_columns.append( c) # always select OLAP Role labels
            continue # no further checking needed.
        if _get_sql_field_name(c) in nonselect_tables:
            continue #skip, this Dim was only included to support an OLAP-Role!
        select_columns.append( c)
    statement = sql.select( columns=select_columns, from_obj=join_clause)
    # add fact filters, if not already included with joins
    if fact_filters_unprocessed:
        for filter_urlencoded in fact_filters:
            start_bind = len(binds)
            filter_tuple = parameters.get_filter_condition_sqlalchemy_pgsql_string(
                json_python_types
                ,filter_urlencoded
                ,start_bind)
            filter_expression, filter_binds = filter_tuple
            # replace web 'field' name with 'table.column'
            web_field = parameters.get_filter_processed_3tuple(json_python_types, filter_urlencoded)[0]
            var, table_name = variables_and_tables_by_web_name[web_field]
            fact_column = '.'.join([table_name, var['column']])
            rewritten_expression = filter_expression.lstrip().replace(web_field, fact_column)
            sa_text = sql.text(rewritten_expression)
            statement = statement.where(sa_text)
            binds.update(filter_binds)
        fact_filters_unprocessed = False #now, they've been processed!

    return statement, binds

def _is_olap_role( column_element):
    """
    Utility function returning true if column is of format: "alias.field_name"
    """
    if isinstance( column_element, sql.sql.elements.Label):
        #check if element is: schema.table.field or just alias.field
        string_representation = str(column_element)
        fields = string_representation.split('.')
        if len(fields) == 2:
            return True
    return False #An OLAP-Role alias is ALWAYS a SQLAlchemy Label

def _get_sql_field_name( column_element):
    """
    Utility function returning the string name of a SQLAlchemy ColumnElement

    Keyword Parameters:
    column_element  -- SQLAlchemy ColumnElement representing a physical
      database field selected by some method.

    Exceptions:
    FieldOlapRole  -- raised when column_element is an Aliased Table field
    """
    if isinstance(column_element, sql.sql.elements.Label):
        #check if element is: schema.table.field or just alias.field
        string_representation = str(column_element)
        fields = string_representation.split('.')
        if len(fields) == 3:
            schema, table_name, field = fields
            return table_name
        raise FieldOlapRole(c)
    # column_element must otherwise be a Column
    return column_element.table.name

def _get_unattached_columns(fact_name, variables_by_table_name, aliases, model):
    """
    Construct SQLAlchemy Columns for Fact table & non-aliased Dimensions

    Columns describe a field, but are not yet associated with a Table.

    Keyword Parameters:
    fact_name  -- String, representing name of the Fact table that
      SQLAlchemy Columns representing measured (or calculated) fact
      values will be constructed for.
    variable_by_table_name  -- Dict of lists, indexed by name of the
      table which contains the variables. Lists contain DWSupport
      'variable' objects related to the named table.
    aliases   -- list of Strings, representing Dimension tables that
      are actually OLAP Roles (aliases for another dimension). No
      Columns will be constructed for these table entries.
    model  -- dictionary of lists, representing warehouse configuration
      model.

    >>> from pprint import pprint
    >>> example_fact_name = 'great_fact'
    >>> example_dim_name = 'useful_dim'
    >>> example_role_name = 'occasionally_useful_dim'
    >>> vars_by_tab = {example_fact_name: [{'python_type': 'float'
    ...                                     ,'table': example_fact_name
    ...                                     ,'id': 2, 'title': 'measured_time_in_secs'
    ...                                     ,'column': 'measured_time_in_secs'} ]
    ...                ,example_dim_name: [{'python_type': 'str'
    ...                                     ,'table': example_dim_name
    ...                                     ,'id': 1, 'title': 'useful_name'
    ...                                     ,'column': 'useful_name'} ]
    ...                ,example_role_name: [{'python_type': 'str'
    ...                                     ,'table': example_role_name
    ...                                     ,'id': 1, 'title': 'useful_name'
    ...                                     ,'column': 'useful_name'} ] }
    >>> aliases = [example_role_name]
    >>> model_no_custom_ids = {'variable_custom_identifiers': []}
    >>> tup = _get_unattached_columns(example_fact_name, vars_by_tab, aliases, model_no_custom_ids)
    >>> # Check output
    >>> columns, columns_by_table_name = tup
    >>> columns # doctest: +ELLIPSIS
    [Column('measured_time_in_secs', NullType(), table=None), <sqlalchemy.sql.elements.Label object at 0x...>]
    >>> pprint(columns_by_table_name) # doctest: +ELLIPSIS
    {'great_fact': [Column('measured_time_in_secs', NullType(), table=None)],
     'useful_dim': [<sqlalchemy.sql.elements.Label object at 0x...>]}
    >>> # Confirm fact dimensional field has been correctly labeled
    >>> [c.name for c in columns_by_table_name['useful_dim']] #with default/generated ID
    ['useful_dim$useful_name']
    >>> # Check output, with a customized Dimension field name
    >>> model_custom_id = {'variable_custom_identifiers': [
    ...     { 'id': 'used_name', 'table': 'useful_dim', 'column': 'useful_name'}]}
    >>> tup2 = _get_unattached_columns(example_fact_name, vars_by_tab, aliases, model_custom_id)
    >>> # Check output
    >>> columns, columns_by_table_name = tup2
    >>> columns # doctest: +ELLIPSIS
    [Column('measured_time_in_secs', NullType(), table=None), <sqlalchemy.sql.elements.Label object at 0x...>]
    >>> pprint(columns_by_table_name) # doctest: +ELLIPSIS
    {'great_fact': [Column('measured_time_in_secs', NullType(), table=None)],
     'useful_dim': [<sqlalchemy.sql.elements.Label object at 0x...>]}
    >>> # Confirm fact dimensional field has been correctly labeled
    >>> [c.name for c in columns_by_table_name['useful_dim']] #with custom ID
    ['used_name']
    >>> # Check output, with a customized Fact field name
    >>> model_custom_fact_id = {'variable_custom_identifiers': [
    ...     { 'id': 'seconds', 'table': 'great_fact', 'column': 'measured_time_in_secs'}]}
    >>> tup3 = _get_unattached_columns(example_fact_name, vars_by_tab, aliases, model_custom_fact_id)
    >>> # Check output
    >>> columns, columns_by_table_name = tup3
    >>> columns # doctest: +ELLIPSIS
    [<sqlalchemy.sql.elements.Label object at 0x...>, <sqlalchemy.sql.elements.Label object at 0x...>]
    >>> pprint(columns_by_table_name) # doctest: +ELLIPSIS
    {'great_fact': [<sqlalchemy.sql.elements.Label object at 0x...>],
     'useful_dim': [<sqlalchemy.sql.elements.Label object at 0x...>]}
    >>> # Confirm fact field has been correctly labeled
    >>> [c.name for c in columns_by_table_name['great_fact']] #with custom ID
    ['seconds']
    >>> # Confirm fact dimensional field has been correctly labeled
    >>> [c.name for c in columns_by_table_name['useful_dim']] #with default/generated ID
    ['useful_dim$useful_name']
    """
    #compose SQL column definitions, to be select (excluding OLAP-Roles)
    columns = []
    columns_by_table_name = {}
    table_names = list(variables_by_table_name.keys())
    base_tables_sorted = [name for name in table_names if name not in aliases]
    base_tables_sorted.sort() #stabilize column order,for ease of testing
    for table_name in base_tables_sorted:
        columns_for_table = []
        for table_variable in variables_by_table_name[ table_name]:
            table_name = table_variable['table']
            field_name = table_variable['column']
            column = sql.Column( field_name)
            # override the variable ID, if DWSupport specifies a custom ID
            custom_web_name = util.get_custom_variable_name(table_variable, model)
            if custom_web_name is not None: #TODO: refactor above, to reduce duplication
                column = column.label(custom_web_name)
            # check if the variable's table is the Fact table, or a dimension
            if table_name != fact_name:
                # dimension fields: prefix with the dimension name (this makes
                # the field readily identifiable by a user,across many
                # different cubes)
                field_name = table_variable['column'] #friendly,human identifier
                alias = util.prefix_field_name( field_name, table_name)
                # override the variable ID, if DWSupport specifies a custom ID
                custom_web_name = util.get_custom_variable_name(table_variable, model)
                if custom_web_name is not None: #TODO: refactor above, to reduce duplication
                    alias = custom_web_name
                column = column.label( alias)
            columns.append( column)
            columns_for_table.append( column)
        columns_by_table_name[table_name] = columns_for_table
    return columns, columns_by_table_name

def _get_attached_fact_cols_dims_tuple(fact_name, schema, columns, columns_by_table_name, variables_by_table_name, associations_by_parent, aliases, model):
    """
    Makes Fact+Dim SQLAlchemy Tables & updates SQLAlchemy Columns list

    column updates comprise: mapping to tables, labeling with aliases,
    and appending additional labeled SQLAlchemy Columns representing
    fields from the Fact table's OLAP-Roles(aliased Dimensional lookups)

    Keyword Parameters:
    fact_name  -- String, representing name of the Fact table.
    schema  -- String, representing name of db schema where all fact and
      dimension tables are physically located.
    columns  -- list of unlabeled SQLAlchemy Columns, without table
      mapping info, for the Fact table fields and fields from all
      fact Dimensions which are not OLAP Roles (e.g.: Dimension bases)
    columns_by_table_name  -- Dict of lists, indexed by table name.
      Lists consist of reference to relevant 'column' parameter items
    variables_by_table_name  -- Dict of lists, indexed by name of the
      table which contains the variables. Lists contain DWSupport
      'variable' objects related to the named table.
    associations_by_parent  --  Dict of warehouse support 'association'
      DTOs by parent table_name.
    aliases   -- list of Strings, representing Dimension tables that
      are actually OLAP Roles (aliases for another dimension). No
      Columns will be constructed for these table entries.
    model  -- dictionary of lists, representing warehouse configuration
      model.

    >>> from pprint import pprint
    >>> from copy import deepcopy
    >>> example_fact_name = 'great_fact'
    >>> example_fact_field = sql.Column('measured_time_in_secs')
    >>> example_dim_name = 'useful_dim'
    >>> # expect dimension columns to come pre-labeled
    >>> example_dimension_field = sql.Column('useful_name').label('useful_dim$useful_name')
    >>> # test with copies of above columns. Function modifies its inputs
    >>> all_cols = [deepcopy(example_fact_field), deepcopy(example_dimension_field)]
    >>> cols_by_tab = {example_fact_name: [all_cols[0]]
    ...                ,example_dim_name: [all_cols[1]] }
    >>> example_role_name = 'occasionally_useful_dim'
    >>> vars_by_tab = {example_fact_name: [{'python_type': 'float'
    ...                                     ,'table': example_fact_name
    ...                                     ,'id': 2, 'title': 'measured_time_in_secs'
    ...                                     ,'column': 'measured_time_in_secs'} ]
    ...                ,example_dim_name: [{'python_type': 'str'
    ...                                     ,'table': example_dim_name
    ...                                     ,'id': 1, 'title': 'useful_name'
    ...                                     ,'column': 'useful_name'} ]
    ...                ,example_role_name: [{'python_type': 'str'
    ...                                     ,'table': example_role_name
    ...                                     ,'id': 1, 'title': 'useful_name'
    ...                                     ,'column': 'useful_name'} ] }
    >>> assocs_by_parent = {example_dim_name: {'type': 'fact dimension'
    ...                                        ,'parent': example_dim_name
    ...                                        ,'table': example_fact_name
    ...                                        ,'column': 'useful_whid'
    ...                                        ,'parent_column': 'useful_whid'}
    ...                     ,example_role_name: {'type': 'fact dimension role'
    ...                                          ,'parent': example_dim_name
    ...                                          ,'table': example_fact_name
    ...                                          ,'column': 'occasionally_useful_whid'
    ...                                          ,'parent_column': 'useful_whid'} }
    >>> aliases = [example_role_name]
    >>> model_no_custom = {'variable_custom_identifiers': []}
    >>> tup = _get_attached_fact_cols_dims_tuple(example_fact_name, 'dw', all_cols, cols_by_tab, vars_by_tab, assocs_by_parent, aliases, model_no_custom)
    >>> len(tup) #Check function output
    3
    >>> output_fact_table, output_cols, output_dim_assoc_pairs = tup
    >>> type(output_fact_table) #Check the table
    <class 'sqlalchemy.sql.schema.Table'>
    >>> output_fact_table.name
    'great_fact'
    >>> output_fact_table.schema
    'dw'
    >>> output_fact_table.metadata
    MetaData(bind=None)
    >>> list_of_cols = [c for c in output_fact_table.columns]
    >>> list_of_cols.sort(key=str) # stabilize order, for easy comparison
    >>> list_of_cols
    [Column('measured_time_in_secs', NullType(), table=<great_fact>), Column('occasionally_useful_whid', NullType(), table=<great_fact>), Column('useful_whid', NullType(), table=<great_fact>)]
    >>> # Now, check the columns
    >>> output_cols # doctest: +ELLIPSIS
    [Column('measured_time_in_secs', NullType(), table=<great_fact>), <sqlalchemy.sql.elements.Label object at ...>, <sqlalchemy.sql.elements.Label object at ...>]
    >>> # check fact dimension field labeled with a default/generated unique id
    >>> output_cols[2].name
    'occasionally_useful_dim$useful_name'
    >>> # Last, check the dimension/lookup pairs
    >>> pprint(output_dim_assoc_pairs) # doctest: +ELLIPSIS
    [(Table('useful_dim', MetaData(bind=None), Column('useful_name', NullType(), table=<useful_dim>), Column('useful_whid', NullType(), table=<useful_dim>), schema='dw'),
      {'column': 'useful_whid',
       'parent': 'useful_dim',
       'parent_column': 'useful_whid',
       'table': 'great_fact',
       'type': 'fact dimension'}),
     (<sqlalchemy.sql.selectable.Alias at ...; occasionally_useful_dim>,
      {'column': 'occasionally_useful_whid',
       'parent': 'useful_dim',
       'parent_column': 'useful_whid',
       'table': 'great_fact',
       'type': 'fact dimension role'})]
    >>> # Check custom identifiers for fact Dimension Role fields
    >>> model_custom_id = {'variable_custom_identifiers': [
    ...     { 'id': 'occasional_name', 'table': 'occasionally_useful_dim'
    ...      ,'column': 'useful_name'}]}
    >>> all_cols = [deepcopy(example_fact_field), deepcopy(example_dimension_field)]
    >>> cols_by_tab = {example_fact_name: [all_cols[0]]
    ...                ,example_dim_name: [all_cols[1]] }
    >>> tup2 = _get_attached_fact_cols_dims_tuple(example_fact_name, 'dw', all_cols, cols_by_tab, vars_by_tab, assocs_by_parent, aliases, model_custom_id)
    >>> len(tup2) #Check function output
    3
    >>> output_fact_table, output_cols, output_dim_assoc_pairs = tup2
    >>> type(output_fact_table) #Check the table
    <class 'sqlalchemy.sql.schema.Table'>
    >>> output_fact_table.name
    'great_fact'
    >>> output_fact_table.schema
    'dw'
    >>> output_fact_table.metadata
    MetaData(bind=None)
    >>> list_of_cols = [c for c in output_fact_table.columns]
    >>> list_of_cols.sort(key=str) # stabilize order, for easy comparison
    >>> list_of_cols
    [Column('measured_time_in_secs', NullType(), table=<great_fact>), Column('occasionally_useful_whid', NullType(), table=<great_fact>), Column('useful_whid', NullType(), table=<great_fact>)]
    >>> # Now, check the columns
    >>> output_cols # doctest: +ELLIPSIS
    [Column('measured_time_in_secs', NullType(), table=<great_fact>), <sqlalchemy.sql.elements.Label object at ...>, <sqlalchemy.sql.elements.Label object at ...>]
    >>> # check fact dimension field labeled with the customized ID
    >>> output_cols[2].name
    'occasional_name'
    >>> # Last, check the dimension/lookup pairs
    >>> pprint(output_dim_assoc_pairs) # doctest: +ELLIPSIS
    [(Table('useful_dim', MetaData(bind=None), Column('useful_name', NullType(), table=<useful_dim>), Column('useful_whid', NullType(), table=<useful_dim>), schema='dw'),
      {'column': 'useful_whid',
       'parent': 'useful_dim',
       'parent_column': 'useful_whid',
       'table': 'great_fact',
       'type': 'fact dimension'}),
     (<sqlalchemy.sql.selectable.Alias at ...; occasionally_useful_dim>,
      {'column': 'occasionally_useful_whid',
       'parent': 'useful_dim',
       'parent_column': 'useful_whid',
       'table': 'great_fact',
       'type': 'fact dimension role'})]
    """
    metadata_garbage = sql.MetaData()#(the md workspace automatically tracks db
    # relations & ensures the SQL output makes sense. We dont directly
    # manipulate the md object;it's just along for the ride & keeps us on track

    # create SQLAlchemy Tables
    fact_table = None
    dimension_association_tuples = []
    processed_dimension_tables_by_name = {}
    # ensure OLAP-roles come last... (below design depends on that.)
    unordered_table_names = variables_by_table_name.keys()
    fact_and_dim_dwsupport_table_names, role_dwsupport_table_names = [], []
    for name in unordered_table_names:
        if name in aliases:
            role_dwsupport_table_names.append( name)
            continue #done. go bin the next name
        fact_and_dim_dwsupport_table_names.append( name)
    facts_dims_then_role_names = list(fact_and_dim_dwsupport_table_names
                                      + role_dwsupport_table_names )
    # Create SQLAlchemy Tables for: fact_table & all dimension tables
    for dwsupport_table_name in facts_dims_then_role_names:
        if dwsupport_table_name == fact_name:
            construct_table = fact_name
            dwsupport_table_association = None#if construct_table *is* the fact
            # then there is no corresponding 'association'/lookup.
        else:
            # table is a lookup. retrieve its relationship to the Fact table
            msg = ('Every associations_by_parent key ({}) must also be a key'
                   ' in variables_by_table_name!').format(dwsupport_table_name)
            assert dwsupport_table_name in associations_by_parent, msg
            construct_table = dwsupport_table_name
            dwsupport_table_association = associations_by_parent[dwsupport_table_name]
            
            # Additionally, check if lookup is an alias (not a physical table)
            association_parent_table_name = dwsupport_table_association['parent']
            # if name is not physical, construct physical Dimension instead
            dwsupport_table_name_is_a_role = ( association_parent_table_name != dwsupport_table_name )
            if dwsupport_table_name_is_a_role:
                construct_table = association_parent_table_name
        # construct table (and maybe update columns)
        try:
            table_with_schema, columns = _get_sqlalchemy_table_plus_mapped_columns(
                 construct_table
                ,fact_name
                ,schema
                ,metadata_garbage
                ,processed_dimension_tables_by_name
                ,dwsupport_table_name
                ,columns #TODO: remove mutating columns anti-pattern
                ,columns_by_table_name
                ,variables_by_table_name
                ,associations_by_parent
                ,model
                ,dwsupport_table_association
            )
        except ExceptionFactSQLAlchemyTable as e:
            fact_table = e.table
            continue #skip, to next table
        dimension_association = associations_by_parent[dwsupport_table_name]
        dimension_association_tuple = (table_with_schema, dimension_association)
        dimension_association_tuples.append( dimension_association_tuple)
        #add the Table definition to the dimensions map,by explicit variable name
        processed_dimension_tables_by_name[dwsupport_table_name] = table_with_schema
    return fact_table, columns, dimension_association_tuples

def _get_sqlalchemy_table_plus_mapped_columns(table_name, fact_name, schema, metadata_garbage, processed_dimension_tables_by_name, dwsupport_table_name, columns, columns_by_table_name, variables_by_table_name, associations_by_parent, model, dwsupport_table_association=None):
    """
    create SQLAlchemy tables + column labels

    FIXME: refactor for code comprehension & maintainability

    Keyword Parameters:
    table_name  -- String, representing name of the table to be created
    fact_name  -- String, representing name of the Fact table.
    schema  -- String, representing name of db schema where all fact and
      dimension tables are physically located.
    metadata_garbage  -- SQLAlchemy MetaData object, containing logical
      model of interrelationships between SQLAlchemy created by previous
      evocations of this function.
    processed_dimension_tables_by_name  -- Dict of SQLAlchemy Tables,
      indexed by table name. Contains Tables created by previous
      evocations of this function as compiled by an external process.
    dwsupport_table_name  -- String, representing the direct name of the
      DWSupport 'table' being created. May be the same as 'table_name',
      or may be the name of an OLAP-Role which is based off 'table_name'
    columns  -- list of unlabeled SQLAlchemy Columns, without table
      mapping info, for the Fact table fields and fields from all
      fact Dimensions which are not OLAP Roles (e.g.: Dimension bases)
    columns_by_table_name  -- Dict of lists, indexed by table name.
      Lists consist of reference to relevant 'column' parameter items
    variables_by_table_name  -- Dict of lists, indexed by name of the
      table which contains the variables. Lists contain DWSupport
      'variable' objects related to the named table.
    associations_by_parent  --  Dict of warehouse support 'association'
      DTOs by parent table_name.
    model  -- dictionary of lists, representing warehouse configuration
      model.
    dwsupport_table_association  -- DWSupport 'association' DTO
      describing relationship between Fact & the table to be created
      (Default: None)

    Exceptions:
    ExceptionFactSQLAlchemyTable -- function has built a table for
     fact_name, and no alterations to columns needed

    >>> from pprint import pprint
    >>> md = sql.MetaData()
    >>> table = 'date_dim'
    >>> fact = 'test_fact'
    >>> schema = 'foo'
    >>> processed = {}
    >>> var_table = 'date_dim'
    >>> cols = [sql.Column('month_name'), sql.Column('year'), sql.Column('test_measure_kg')]
    >>> cols_by_table = {'date_dim':cols[0:2],'test_fact':[cols[2]]}
    >>> var_by_table = {'date_dim':[ {'python_type': 'str', 'table': 'date_dim'
    ...                               ,'id': 1, 'title': 'month_name'
    ...                               ,'column': 'month_name'}
    ...                             ,{'python_type': 'int', 'table': 'date_dim'
    ...                               ,'id': 2, 'title': 'year'
    ...                               ,'column': 'year'}]
    ...                 ,'test_fact':[ {'python_type': 'float'
    ...                                 ,'table': 'test_fact', 'id': 3
    ...                                 ,'title': 'test_measure_kg'
    ...                                 ,'column': 'test_measure_kg'}] }
    >>> assoc_by_parent = {'date_dim': { 'type': 'fact dimension'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'} }
    >>> variable_assoc = None
    >>> model_no_custom_ids = {'variable_custom_identifiers': []}
    >>> sa_table, mapped_labeled_cols = _get_sqlalchemy_table_plus_mapped_columns( table, fact, schema, md, processed, var_table, cols, cols_by_table, var_by_table, assoc_by_parent, model_no_custom_ids, variable_assoc)
    >>> str(sa_table)
    'foo.date_dim'
    >>> pprint([c for c in mapped_labeled_cols])
    [Column('month_name', NullType(), table=<date_dim>),
     Column('year', NullType(), table=<date_dim>),
     Column('test_measure_kg', NullType(), table=None)]
    >>> table = 'date_dim' #Test again, this time with an OLAP-Role
    >>> processed = {'date_dim': sa_table } #Role must be provided a processed Dim
    >>> var_table = 'special_date_dim' #reuse the previous md
    >>> var_by_table = {'special_date_dim':[ {'python_type': 'str'
    ...                                       ,'table': 'special_date_dim'
    ...                                       ,'id': 4, 'title': 'month_name'
    ...                                       ,'column': 'month_name'}
    ...                                      ,{'python_type': 'int'
    ...                                       ,'table': 'special_date_dim'
    ...                                       ,'id': 5, 'title': 'year'
    ...                                       ,'column': 'year'}]
    ...                 ,'test_fact':[ {'python_type': 'float'
    ...                                 ,'table': 'test_fact', 'id': 3
    ...                                 ,'title': 'test_measure_kg'
    ...                                 ,'column': 'test_measure_kg'}] }
    >>> assoc_by_parent = {'date_dim': { 'type': 'fact dimension'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'}
    ...                   ,'special_date_dim': { 'type': 'fact dimension role'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'} }
    >>> variable_assoc = assoc_by_parent['special_date_dim']
    >>> sa_table, mapped_labeled_cols = _get_sqlalchemy_table_plus_mapped_columns( table, fact, schema, md, processed, var_table, cols, cols_by_table, var_by_table, assoc_by_parent, model_no_custom_ids, variable_assoc)
    >>> str(sa_table)
    ''
    >>> pprint([str(c) for c in mapped_labeled_cols])
    ['date_dim.month_name',
     'date_dim.year',
     'test_measure_kg',
     'special_date_dim.month_name',
     'special_date_dim.year']
    >>> md = sql.MetaData() # Test again, this time Dim has a user-visible whid
    >>> processed = {}
    >>> var_table = 'date_dim'
    >>> cols = [sql.Column('month_name'), sql.Column('year'), sql.Column('test_measure_kg')]
    >>> cols_by_table = {'date_dim':cols[0:2],'test_fact':[cols[2]]}
    >>> var_by_table = {'date_dim':[ {'python_type': 'str', 'table': 'date_dim'
    ...                               ,'id': 1, 'title': 'month_name'
    ...                               ,'column': 'month_name'}
    ...                             ,{'python_type': 'int', 'table': 'date_dim'
    ...                               ,'id': 2, 'title': 'year'
    ...                               ,'column': 'year'}
    ...                             ,{'python_type': 'int', 'table': 'date_dim'
    ...                               ,'id': 3, 'title': 'Date Whid'
    ...                               ,'column': 'date_whid'}]
    ...                 ,'test_fact':[ {'python_type': 'float'
    ...                                 ,'table': 'test_fact', 'id': 4
    ...                                 ,'title': 'test_measure_kg'
    ...                                 ,'column': 'test_measure_kg'}] }
    >>> assoc_by_parent = {'date_dim': { 'type': 'fact dimension'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'} }
    >>> variable_assoc = None
    >>> sa_table, mapped_labeled_cols = _get_sqlalchemy_table_plus_mapped_columns( table, fact, schema, md, processed, var_table, cols, cols_by_table, var_by_table, assoc_by_parent, model_no_custom_ids, variable_assoc)
    >>> str(sa_table)
    'foo.date_dim'
    >>> pprint([c for c in mapped_labeled_cols]) #TODO: Variables doesnt show it either.. but do we *want* to see date_whid here? We do show it for the Role...
    [Column('month_name', NullType(), table=<date_dim>),
     Column('year', NullType(), table=<date_dim>),
     Column('test_measure_kg', NullType(), table=None)]
    >>> table = 'date_dim' #Test user-visible whid again, with an OLAP-Role
    >>> processed = {'date_dim': sa_table } #Role must be provided a processed Dim
    >>> var_table = 'special_date_dim' #reuse the previous md
    >>> var_by_table = {'special_date_dim':[ {'python_type': 'str'
    ...                                       ,'table': 'special_date_dim'
    ...                                       ,'id': 5, 'title': 'month_name'
    ...                                       ,'column': 'month_name'}
    ...                                      ,{'python_type': 'int'
    ...                                       ,'table': 'special_date_dim'
    ...                                       ,'id': 6, 'title': 'year'
    ...                                       ,'column': 'year'}
    ...                                      ,{'python_type': 'int'
    ...                                       ,'table': 'special_date_dim'
    ...                                       ,'id': 7, 'title': 'Special Data Whid'
    ...                                       ,'column': 'date_whid'}]
    ...                 ,'test_fact':[ {'python_type': 'float'
    ...                                 ,'table': 'test_fact', 'id': 3
    ...                                 ,'title': 'test_measure_kg'
    ...                                 ,'column': 'test_measure_kg'}] }
    >>> assoc_by_parent = {'date_dim': { 'type': 'fact dimension'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'}
    ...                   ,'special_date_dim': { 'type': 'fact dimension role'
    ...                                 ,'parent': 'date_dim'
    ...                                 ,'table': 'test_fact'
    ...                                 ,'column': 'date_whid'
    ...                                 ,'parent_column': 'date_whid'} }
    >>> variable_assoc = assoc_by_parent['special_date_dim']
    >>> sa_table, mapped_labeled_cols = _get_sqlalchemy_table_plus_mapped_columns( table, fact, schema, md, processed, var_table, cols, cols_by_table, var_by_table, assoc_by_parent, model_no_custom_ids, variable_assoc)
    >>> str(sa_table)
    ''
    >>> pprint([str(c) for c in mapped_labeled_cols])
    ['date_dim.month_name',
     'date_dim.year',
     'test_measure_kg',
     'special_date_dim.month_name',
     'special_date_dim.year',
     'special_date_dim.date_whid']
    """
    try:
        # dwsupport_table_name is a dimension Alias if table_name is already processed.
        # FIXME: (this method assumes base dim's processed first, which is bad design)
        base_dimension_name = table_name
        table_with_schema = processed_dimension_tables_by_name[base_dimension_name]
        # simply alias the existing table
        role_name = dwsupport_table_name
        table_with_schema = table_with_schema.alias( role_name)
        # add the aliased columns to our selection list
        if not role_name in columns_by_table_name.keys():
            role_columns = []
            for column in table_with_schema.columns:
                role_variables = variables_by_table_name[role_name]
                role_variable_field_names = [v['column'] for v in role_variables]
                for variable in role_variables:
                    pk_field_name = dwsupport_table_association['parent_column']
                    pk_as_sql_alias = '{}.{}'.format(role_name, pk_field_name)
                    if (str(column) == pk_as_sql_alias
                            and pk_field_name not in role_variable_field_names):
                        #skip the role's primary key field, if it was added by
                        # sqlgenerator just for Joining &isnt in DWSupport list
                        break # skip adding
                    variable_column_as_sql_alias = '{}.{}'.format(role_name, variable['column'])
                    def _get_field_name(original_variable, role_name, model):
                        variable = dict(original_variable)
                        field_name = variable['column']
                        alias = util.prefix_field_name( field_name, role_name)
                        variable['column'] = alias #TODO: fix this terrible design
                        custom_id = util.get_custom_variable_name(
                            variable
                            ,model)
                        if custom_id is not None:
                            alias = custom_id
                        return alias
                    if str(column) == variable_column_as_sql_alias:
                        alias = _get_field_name(variable, role_name, model)
                        column = column.label( alias)
                        role_columns.append( column)# add aliased Role column
                        break
                else:
                    msg = "Unable to find '{}' dwsupport variable, for table {}." #TODO: make into a local class
                    raise ValueError(msg.format(str(column),role_name))
            columns.extend( role_columns)
            columns_by_table_name[role_name]=role_columns
    except KeyError:# dimension's not yet procesed (or is a fact table)
        # extract the raw columns. (For some reason only a ColumnClause may be
        # mapped to a Table,not a Label - even though both extend ColumnElement
        table_columns = []
        for labeled_column in columns_by_table_name[table_name]:
            table_columns.extend( labeled_column.base_columns)
        table_with_schema = sql.Table( table_name, metadata_garbage
                               ,*table_columns #include as args,all column objs
                               ,schema=schema)
        if table_name == fact_name:
            # add *all* the dimension key columns
            for dim_table_name in associations_by_parent.keys():
                association = associations_by_parent[dim_table_name]
                field_name_with_dim_lookup = association['column']
                field_with_lookup = sql.Column( field_name_with_dim_lookup)
                table_with_schema.append_column( field_with_lookup)
            fact_table = table_with_schema
            raise ExceptionFactSQLAlchemyTable(fact_table)#FIXME: exceptions should not be routine!
        # table must be a dimension ..
        dimension_association = associations_by_parent[ table_name]
        # .. add the dimension field,defining the key values(used for join)
        field_name = dimension_association['parent_column']
        table_with_schema.append_column( sql.Column(field_name))
    return table_with_schema, columns
