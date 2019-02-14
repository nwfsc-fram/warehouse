"""
Module providing a Falcon resource for NMFS/FIS InPort XML metadata

Copyright (C) 2016 ERT Inc.
"""
import falcon
from lxml import etree

from . import (
    source
    ,parameters as source_parameters
    ,variables as source_variables
)
from api.auth import auth
from api.resources.source.warehouse import warehouse

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

route = "metadata.xml"
"""
String representing the URI path for this endpoint

E.g., "source/{id}/metadata.xml"
"""

class Metadata():
    """
    Falcon resource object, representing dataset InPort XML metadata
    """

    def on_get(self, request, response, **kwargs):
        """
        Falcon resource method for handling the HTTP request GET method

        Falcon API provides: parameters embedded in URL via a keyword
        args dict, as well as convenience class variables falcon.HTTP_*
        """
        with warehouse.get_source_model_session() as current_model:
            #get Source dataset object, referenced in URL path
            sources = source.SourceUtil.get_list_of_data_sources(
                 request.url
                ,auth.get_user_id(request)
                ,current_model)
            dataset_id = source_parameters.get_requested_dataset_id(sources
                                                                    ,request
                                                                    ,response
                                                                    ,kwargs)
            if warehouse.is_warehouse(dataset_id):
                msg = 'Metadata.xml not available for source ID: '+dataset_id
                raise falcon.HTTPInvalidParam(msg, 'source')
            dataset = None
            for table in current_model['tables']:
                table_id = '{}.{}'.format(table['project'],table['name'])
                if table_id == dataset_id:
                    dataset = table
                    break
            #get DWSupport Project data transfer object representing dataset proj.
            dataset_project = None
            for project in current_model['projects']:
                if project['name'] == dataset['project']:
                    dataset_project = project
                    break
            #get variable for the Source dataset
            variables = source_variables.get_list_of_variables(dataset_id)
            #return generated XML
            response.content_type = 'text/xml'
            response.body = to_inport_xml(dataset, variables, dataset_project)

def _to_xml(number):
    """
    convert Python number to XML String representation

    Keyword Parameters:
    number  -- Python numeric variable

    >>> _to_xml(0)
    '0'
    >>> _to_xml(0.09834894752)
    '0.09834894752'
    >>> _to_xml(None)
    ''
    """
    if number is None:
        return ''
    return str(number)

def _xml_element(name, text=None, attributes={}):
    """
    returns lxml Element with referenced name, text value & attributes

    Keyword Parameters:
    name  -- String, representing name of the new element
    text  -- String, representing the text value of the new element as
      returned by the '_to_xml' utility function
    attributes  -- Dictionary of strings by attribute name, to be added
      to the returned element

    >>> out = _xml_element("out", text="test")
    >>> etree.tostring(out)
    b'<out>test</out>'
    >>> out = _xml_element("out")
    >>> etree.tostring(out)
    b'<out/>'
    >>> out = _xml_element("out", text='')
    >>> etree.tostring(out)
    b'<out></out>'
    >>> out = _xml_element("out", attributes={'other':'value'})
    >>> etree.tostring(out)
    b'<out other="value"/>'
    """
    element = etree.Element(name, **attributes)
    if text is not None:
        element.text = text
    return element

def to_inport_xml(table, variables, project):
    """
    Generate NMFS/FIS InPort XML Format document for DWSupport table

    Document represents an Entity Insert if no table
    inport_entity_id is available. If an inport_entity_id is available
    the document will represent an Entity Update.
    per: https://inport.nmfs.noaa.gov/inport/help/xml-loader

    Keyword Parameters:
    table  -- Warehouse support data transfer object, representing a
      table configured in DWSupport schema.
    variables  -- list of Warehouse support DTOs, representing table's
      variables.
    project  -- Warehouse support DTO, representing project associated
      with 'table'

    >>> import datetime
    >>> from pprint import pprint, pformat
    >>> import difflib
    >>> # Test XML generation
    >>> to_str_list = lambda s: pformat(s).split('\\n') #helper function, for testing with difflib
    >>> t = {'contact': 'Name: FRAM Data Team '
    ...                 '<nmfs.nwfsc.fram.data.team@noaa.gov>'
    ...      ,'name': 'person_dim'
    ...      ,'project': 'warehouse'
    ...      ,'description': 'Person Dimension'
    ...      ,'rows': 373
    ...      ,'selectable': True
    ...      ,'inport_id': None
    ...      ,'inport_replacement_project_id': None
    ...      ,'type': 'dimension'
    ...      ,'updated': datetime.datetime(2016, 4, 5, 21, 21, 15)
    ...      ,'years': None, 'keywords': 'pacific,marine,demographic'
    ...      ,'restriction': 'otherRestrictions', 'usage_notice':
    ...   'Courtesy: Northwest Fisheries Science Center, NOAA Fisheries'
    ...      ,'update_frequency': 'continual', 'uuid': None}
    >>> vars = [{ 'column':'full_name', 'title':'Full Name'
    ...         ,'python_type': 'str', 'physical_type': 'VARCHAR'
    ...         ,'table': 'person_dim', 'max_length': 255
    ...         ,'units': 'Unspecified', 'precision': None
    ...         ,'description': 'Full name of person'
    ...         ,'allowed_values': 'Any'}]
    >>> proj = { 'name': 'warehouse', 'inport_id': None
    ...         ,'title': 'NMFS/NWFSC FRAM Data Warehouse'}
    >>> xml_string1 = to_inport_xml(t, vars, proj)
    >>> pprint(xml_string1)
    ("<?xml version='1.0' encoding='UTF-8'?>\\n"
     '<inport-metadata version="1.0">\\n'
     '  <item-identification>\\n'
     '    <parent-catalog-item-id></parent-catalog-item-id>\\n'
     '    <catalog-item-type>Entity</catalog-item-type>\\n'
     '    <title>person_dim</title>\\n'
     '  </item-identification>\\n'
     '  <entity-information>\\n'
     '    <entity-type>Data Table</entity-type>\\n'
     '    <description>Person Dimension</description>\\n'
     '  </entity-information>\\n'
     '  <data-attributes>\\n'
     '    <data-attribute>\\n'
     '      <name>full_name</name>\\n'
     '      <data-storage-type>VARCHAR</data-storage-type>\\n'
     '      <max-length>255</max-length>\\n'
     '      <precision></precision>\\n'
     '      <status>Active</status>\\n'
     '      <description>Full name of person</description>\\n'
     '      <units>Unspecified</units>\\n'
     '      <allowed-values>Any</allowed-values>\\n'
     '    </data-attribute>\\n'
     '  </data-attributes>\\n'
     '</inport-metadata>\\n')
    >>> # Test XML when Project has an InPort ID
    >>> proj['inport_id'] = 7890
    >>> xml_string2 = to_inport_xml(t, vars, proj) #now, with project id
    >>> diff = difflib.unified_diff(to_str_list(xml_string1)
    ...                             ,to_str_list(xml_string2), n=1
    ...                             ,lineterm="")
    >>> diff_string = '\\n'.join([string for string in diff])
    >>> pprint(diff_string)
    ('--- \\n'
     '+++ \\n'
     '@@ -3,3 +3,3 @@\\n'
     "  '  <item-identification>\\\\n'\\n"
     "- '    <parent-catalog-item-id></parent-catalog-item-id>\\\\n'\\n"
     "+ '    <parent-catalog-item-id>7890</parent-catalog-item-id>\\\\n'\\n"
     "  '    <catalog-item-type>Entity</catalog-item-type>\\\\n'")
    >>> # Test XML when Table has an overriding InPort project ID
    >>> t['inport_replacement_project_id'] = 451
    >>> xml_string3 = to_inport_xml(t, vars, proj) #customizes the project ID
    >>> diff = difflib.unified_diff(to_str_list(xml_string2)
    ...                             ,to_str_list(xml_string3), n=1
    ...                             ,lineterm="")
    >>> diff_string = '\\n'.join([string for string in diff])
    >>> pprint(diff_string)
    ('--- \\n'
     '+++ \\n'
     '@@ -3,3 +3,3 @@\\n'
     "  '  <item-identification>\\\\n'\\n"
     "- '    <parent-catalog-item-id>7890</parent-catalog-item-id>\\\\n'\\n"
     "+ '    <parent-catalog-item-id>451</parent-catalog-item-id>\\\\n'\\n"
     "  '    <catalog-item-type>Entity</catalog-item-type>\\\\n'")
    >>> # Test XML when Project & Table have InPort IDs
    >>> t['inport_id'] = 54321 #now, with table InPort Entity ID
    >>> xml_string4 = to_inport_xml(t, vars, proj)
    >>> diff = difflib.unified_diff(to_str_list(xml_string3)
    ...                             ,to_str_list(xml_string4), n=1
    ...                             ,lineterm="")
    >>> diff_string = '\\n'.join([string for string in diff])
    >>> pprint(diff_string)
    ('--- \\n'
     '+++ \\n'
     '@@ -3,3 +3,3 @@\\n'
     "  '  <item-identification>\\\\n'\\n"
     "- '    <parent-catalog-item-id>451</parent-catalog-item-id>\\\\n'\\n"
     "+ '    <catalog-item-id>54321</catalog-item-id>\\\\n'\\n"
     "  '    <catalog-item-type>Entity</catalog-item-type>\\\\n'")
    >>> # Test XML when Table is a Role
    >>> t['type'] = 'dimension role' #now, for a virtual table
    >>> xml_string5 = to_inport_xml(t, vars, proj)
    >>> diff = difflib.unified_diff(to_str_list(xml_string4)
    ...                             ,to_str_list(xml_string5), n=1
    ...                             ,lineterm="")
    >>> diff_string = '\\n'.join([string for string in diff])
    >>> pprint(diff_string)
    ('--- \\n'
     '+++ \\n'
     '@@ -8,3 +8,3 @@\\n'
     "  '  <entity-information>\\\\n'\\n"
     "- '    <entity-type>Data Table</entity-type>\\\\n'\\n"
     "+ '    <entity-type>Data View</entity-type>\\\\n'\\n"
     "  '    <description>Person Dimension</description>\\\\n'")
    >>> # Test XML when Table is a SQL view
    >>> t['type'] = 'fact' #facts named "*_view" are also virtual tables
    >>> t['name'] = 'person_view'
    >>> xml_string6 = to_inport_xml(t, vars, proj)
    >>> diff = difflib.unified_diff(to_str_list(xml_string5)
    ...                             ,to_str_list(xml_string6), n=1
    ...                             ,lineterm="")
    >>> diff_string = '\\n'.join([string for string in diff])
    >>> pprint(diff_string)#entity-type remains View,only title changes
    ('--- \\n'
     '+++ \\n'
     '@@ -5,3 +5,3 @@\\n'
     "  '    <catalog-item-type>Entity</catalog-item-type>\\\\n'\\n"
     "- '    <title>person_dim</title>\\\\n'\\n"
     "+ '    <title>person_view</title>\\\\n'\\n"
     "  '  </item-identification>\\\\n'")
    >>> # Test when Table has column data
    >>> vars = [{ 'column':'full_name', 'title':'Full Name' #Now, check max_length default
    ...         ,'python_type': 'str', 'physical_type': 'VARCHAR'
    ...         ,'table': 'person_dim', 'max_length': None
    ...         ,'units': 'Unspecified', 'precision': None
    ...         ,'description': 'Full name of person'
    ...         ,'allowed_values': 'Any'}]
    >>> xml_string7 = to_inport_xml(t, vars, proj)
    >>> pprint(xml_string7)
    ("<?xml version='1.0' encoding='UTF-8'?>\\n"
     '<inport-metadata version="1.0">\\n'
     '  <item-identification>\\n'
     '    <catalog-item-id>54321</catalog-item-id>\\n'
     '    <catalog-item-type>Entity</catalog-item-type>\\n'
     '    <title>person_view</title>\\n'
     '  </item-identification>\\n'
     '  <entity-information>\\n'
     '    <entity-type>Data View</entity-type>\\n'
     '    <description>Person Dimension</description>\\n'
     '  </entity-information>\\n'
     '  <data-attributes>\\n'
     '    <data-attribute>\\n'
     '      <name>full_name</name>\\n'
     '      <data-storage-type>VARCHAR</data-storage-type>\\n'
     '      <max-length>0</max-length>\\n'
     '      <precision></precision>\\n'
     '      <status>Active</status>\\n'
     '      <description>Full name of person</description>\\n'
     '      <units>Unspecified</units>\\n'
     '      <allowed-values>Any</allowed-values>\\n'
     '    </data-attribute>\\n'
     '  </data-attributes>\\n'
     '</inport-metadata>\\n')
    """
    inport_metadata = etree.Element("inport-metadata", version="1.0")

    #construct required identifiers
    item_identification = etree.Element("item-identification")
    inport_project_id = project['inport_id']
    # check if table has been assigned to a different InPort project
    replacement_project_id = table['inport_replacement_project_id']
    if replacement_project_id:
        inport_project_id = replacement_project_id

    # check if table already has an InPort entity ID
    inport_entity_id = table['inport_id']
    if inport_entity_id:
        # add required Update element
        item_id = _xml_element("catalog-item-id", text=str(inport_entity_id))
    else:
        # add required Insert element
        item_id = _xml_element("parent-catalog-item-id"
                               ,text=_to_xml(inport_project_id))
    item_type = _xml_element("catalog-item-type", text="Entity")
    title = _xml_element("title", text=table['name'])
    item_identification.extend([item_id, item_type, title])

    #construct optional entity info
    entity_information = etree.Element("entity-information")
    entity_type = _xml_element("entity-type", text="Data Table")
    if table['type'] == 'dimension role':
        entity_type.text = "Data View"
    if (table['type'] == 'fact'
            and table['name'].endswith('_view')):
        entity_type.text = "Data View"
    description = _xml_element("description", text=table['description'])
    entity_information.extend([entity_type, description])
    #construct optional attribute info
    data_attributes = etree.Element("data-attributes")
    for variable in variables:
        attribute = etree.Element("data-attribute")
        # add required attribute elements
        name = _xml_element("name", text=variable['column'])
        storage_type = _xml_element("data-storage-type"
                                    ,text=variable['physical_type'])
        max_length_text = '0' #if length unavailable/not applicable, use 0
        if variable['max_length'] is not None:
            max_length_text = str(variable['max_length'])
        max_length = _xml_element("max-length"
                                  ,text=max_length_text)
        status = _xml_element("status", text="Active")
        req_elements = [name, storage_type, max_length, status]
        # add InPort optional elements (Required by FRAM)
        precision = _xml_element("precision"
                                 ,text=_to_xml(variable['precision']))
        description = _xml_element("description", text=variable['description'])
        units = _xml_element("units", text=variable['units'])
        allowed = _xml_element("allowed-values"
                               ,text=variable['allowed_values'])
        optional_elements = [precision, description, units, allowed]
        attribute.extend(req_elements[:3] + optional_elements[:1]
                         + req_elements[3:] + optional_elements[1:])
        data_attributes.append(attribute)
    #add inport-metadata's required (& optional) child elements
    inport_metadata.extend([item_identification
                            ,entity_information
                            ,data_attributes
    ])
    utf8 = 'UTF-8'
    xml_bytes = etree.tostring(inport_metadata, encoding=utf8
                               ,xml_declaration=True, pretty_print=True)
    xml_string = xml_bytes.decode(utf8)
    return xml_string
