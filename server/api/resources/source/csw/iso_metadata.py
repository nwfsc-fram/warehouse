"""
Module providing a ISO:19139 Geographic MetaData endpoint

Copyright (C) 2016 ERT Inc.
"""
import configparser
import collections
import os
from io import StringIO
from tempfile import NamedTemporaryFile

import falcon
from pygeometa import render_template

from api.resources.source import (
    source
    ,parameters as source_parameters
)
from api.auth import auth
from api.resources.source.warehouse import support, warehouse

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

route = "metadata.iso"
"""
String representing the URI path for this endpoint

E.g., "source/{id}/metadata.iso"
"""

class Metadata():
    """
    Falcon resource object, representing dataset ISO-19139 XML metadata
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
            iso_xml = geographic_metadata(dataset, current_model)
            #return generated XML
            response.content_type = 'text/xml'
            response.body = iso_xml

def geographic_metadata(dwsupport_table, dwsupport_model):
    """
    Returns ISO 19139 XML representation of referenced DWSupport 'table'
    """
    dataset = dwsupport_table
    current_model = dwsupport_model
    bounds = support.dto_util.get_table_bounds_tuple(dataset)
    # generate string, representing a Pygeometa m(etadata)c(ontrol)f(ile)
    control_string = _build_control_string(dataset, bounds, current_model)
    # return XML GeographicMetaData
    return _control_string_to_geographic_metadata(control_string)

def _convert_None_to_str(value):
    """
    returns input value or 'None' string value if input is None

    The DictParser representation of a pygeometa MCF can't handle an
    actual value of: None.  All dict keys must be strings.

    >>> _convert_None_to_str('foo')
    'foo'
    >>> _convert_None_to_str('None')
    'None'
    >>> _convert_None_to_str(None)
    'None'
    """
    if value is None:
        return 'None'
    return value

def _build_control_string(dto_table, bounds_4tuple, model):
    """
    returns string representing pygeometa MCF for referenced metadata

    Keyword Parameters:
    dto_table  -- DWSupport 'table' Data Transfer Object, representing
        the Warehoused item to be described.
    bounds_4tuple  -- ordered collection of four floating point numbers
        representing the North, East, South and West lat/long bounds of
        Warehoused item
    model  -- Dict of lists, representing the entire DWSupport
      configuration

    >>> import datetime
    >>> from pprint import pprint
    >>> t = {'updated': datetime.datetime(2016, 4, 25, 15, 31, 43)
    ...     ,'name': 'catch_fact', 'selectable': True, 'type': 'fact'
    ...     ,'project': 'trawl', 'years': '1998-2015', 'inport_id': None
    ...     ,'description': 'abstract in English', 'title': 'Trawl survey catch'
    ...     ,'contact':
    ...      'Name: FRAM Data Team <nmfs.nwfsc.fram.data.team@noaa.gov>'
    ...     ,'rows': 301530, 'keywords': 'pacific,trawl,survey,marine'
    ...     ,'restriction': 'otherRestrictions', 'usage_notice':
    ...      'Courtesy: Northwest Fisheries Science Center, NOAA Fisheries'
    ...     ,'update_frequency': 'continual', 'uuid': None}
    >>> bounds = (79.9, -120.5, 60.0, -129.5)
    >>> model = {'tables': [t], 'projects': [{ 'name': 'trawl'
    ...                                       ,'uuid': '90A-BC-DEF1'}] }
    >>> control_string = _build_control_string(t, bounds, model)
    >>> pprint(control_string)
    ('[metadata]\\n'
     'identifier = None\\n'
     'language = en\\n'
     'charset = utf8\\n'
     'parentidentifier = 90A-BC-DEF1\\n'
     'hierarchylevel = dataset\\n'
     'datestamp = 2016-04-25\\n'
     'dataseturi = '
     'https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json\\n'
     '\\n'
     '[spatial]\\n'
     'datatype = grid\\n'
     'crs = 4326\\n'
     'bbox = -129.5,60.0,-120.5,79.9\\n'
     '\\n'
     '[identification]\\n'
     'language = eng; US\\n'
     'charset = utf8\\n'
     'title_en = Trawl survey catch\\n'
     'abstract_en = abstract in English\\n'
     'keywords_en = pacific,trawl,survey,marine\\n'
     'keywords_type = theme\\n'
     'topiccategory = climatologyMeteorologyAtmosphere\\n'
     'publication_date = 2016-04-25T15:31:43Z\\n'
     'fees = None\\n'
     'accessconstraints = otherRestrictions\\n'
     'rights_en = Courtesy: Northwest Fisheries Science Center, NOAA Fisheries\\n'
     'url = '
     'https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json\\n'
     'temporal_begin = 1998\\n'
     'temporal_end = 2015\\n'
     'status = onGoing\\n'
     'maintenancefrequency = continual\\n'
     '\\n'
     '[contact:main]\\n'
     'organization = FRAM Data Team\\n'
     'url = https://www.nwfsc.noaa.gov/research/divisions/fram\\n'
     'address = 2725 Montlake Boulevard East\\n'
     'city = Seattle\\n'
     'administrativearea = WA\\n'
     'postalcode = 98112\\n'
     'country = US\\n'
     'email = nmfs.nwfsc.fram.data.team@noaa.gov\\n'
     'hoursofservice = 0800h - 1700h PST\\n'
     'contactinstructions = email\\n'
     '\\n'
     '[contact:distribution]\\n'
     'ref = contact:main\\n'
     '\\n'
     '[distribution:warehouse]\\n'
     'url = '
     'https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json\\n'
     'type = WWW:LINK\\n'
     'name = NMFS/FRAM Data Warehouse\\n'
     'description_en = RESTful API; see API notes at '
     'https://www.nwfsc.noaa.gov/data/map\\n'
     'function = download\\n'
     '\\n')
    """
    # data for control file
    source_name = dto_table['name']
    source_identifier = dto_table['uuid']
    project_name = dto_table['project']
    project_uuid = 'None'
    for dto_project in model['projects']: #get UUID for Table's project
        if dto_project['name'] == project_name:
            project_uuid = dto_project['uuid']
            break # exit loop, & continue to prepare control file data
    url = ('https://www.nwfsc.noaa.gov/data/api/v1/source/{}.{}'
           '/selection.json').format(project_name, source_name)
    update_date = dto_table['updated'].strftime('%Y-%m-%d')
    update_timestamp = dto_table['updated'].isoformat()+'Z'
    begin_year, end_year = 'None', 'None'
    if dto_table['years'] is not None:
        begin_year, end_year = support.dto_util.decode_years_to_min_max(
            dto_table['years']
        )
    bounds_north, bounds_east, bounds_south, bounds_west = bounds_4tuple
    pygeometa_bbox = '{},{},{},{}'.format(bounds_west, bounds_south
                                          ,bounds_east, bounds_north)
    title = dto_table['title']
    abstract = dto_table['description']
    keywords = dto_table['keywords']
    restrictions = dto_table['restriction']
    usage_notice = dto_table['usage_notice']
    update_frequency = dto_table['update_frequency']
    # build MCF structure
    config_parser = configparser.ConfigParser()
    config_parser['metadata'] = collections.OrderedDict([
        (key, _convert_None_to_str(value)) for key, value in [
            ('identifier', source_identifier)
            ,('language', 'en')
            ,('charset', 'utf8')
            ,('parentidentifier', project_uuid)
            ,('hierarchylevel', 'dataset')
            ,('datestamp', update_date)
            ,('dataseturi', url)
        ]
    ])
    config_parser['spatial'] = collections.OrderedDict([
        (key, _convert_None_to_str(value)) for key, value in [
            ('datatype', 'grid')
            ,('crs', '4326')# Coordinate Reference System, we use EPSG:4326
            ,('bbox', pygeometa_bbox)
        ]
    ])
    config_parser['identification'] = collections.OrderedDict([
        (key, _convert_None_to_str(value)) for key, value in [
            ('language', 'eng; US')
            ,('charset', 'utf8')
            ,('title_en', title)
            ,('abstract_en', abstract)
            ,('keywords_en', keywords)
            ,('keywords_type', 'theme')
            ,('topiccategory', 'climatologyMeteorologyAtmosphere')
            ,('publication_date', update_timestamp)
            ,('fees', 'None')
            ,('accessconstraints', restrictions)
            ,('rights_en', usage_notice)
            ,('url', url)
            ,('temporal_begin', begin_year)
            ,('temporal_end', end_year)
            ,('status', 'onGoing')
            ,('maintenancefrequency', update_frequency)
        ]
    ])
    config_parser['contact:main'] = collections.OrderedDict([
        ('organization', 'FRAM Data Team')
        ,('url', 'https://www.nwfsc.noaa.gov/research/divisions/fram')
        ,('address', '2725 Montlake Boulevard East')
        ,('city', 'Seattle')
        ,('administrativearea', 'WA')
        ,('postalcode', '98112')
        ,('country', 'US')
        ,('email', 'nmfs.nwfsc.fram.data.team@noaa.gov')
        ,('hoursofservice', '0800h - 1700h PST')
        ,('contactinstructions', 'email')
    ])
    config_parser['contact:distribution'] = {
        'ref': 'contact:main'
    }
    config_parser['distribution:warehouse'] = collections.OrderedDict([
        ('url', url)
        ,('type', 'WWW:LINK')
        ,('name', 'NMFS/FRAM Data Warehouse')
        ,('description_en', 'RESTful API; see API notes at https://www.nwfsc.noaa.gov/data/map')
        ,('function', 'download')
    ])
    # write Config out as a String
    string_buffer = StringIO()
    config_parser.write(string_buffer)
    string_buffer.seek(0)
    return string_buffer.read()

def _control_string_to_geographic_metadata(metadata_control):
    """
    returns ISO Geographic MetaData XML representation of control string

    Keyword Parameters:
    metadata_control  -- String, representing contents of a pygeometa
      'metadata control' file (ConfigParser-style formatting)

    >>> from pprint import pprint
    >>> sample = '''[metadata]
    ... identifier=3f342f64-9348-11df-ba6a-0014c2c00eab
    ... language=en
    ... language_alternate=fr
    ... charset=utf8
    ... parentidentifier=someparentid
    ... hierarchylevel=dataset
    ... datestamp=2014-11-11
    ... dataseturi=http://some/minted/uri
    ... 
    ... [spatial]
    ... datatype=vector
    ... geomtype=point
    ... crs=4326
    ... bbox=-141,42,-52,84
    ... 
    ... [identification]
    ... language=eng; CAN
    ... charset=utf8
    ... title_en=title in English
    ... title_fr=title in French
    ... abstract_en=abstract in English
    ... abstract_fr=abstract in French
    ... keywords_en=kw1 in English,kw2 in English,kw3 in English
    ... keywords_fr=kw1 in French,kw2 in French,kw3 in French
    ... keywords_type=theme
    ... keywords_gc_cst_en=kw1,kw2
    ... keywords_gc_cst_fr=kw1,kw2
    ... topiccategory=climatologyMeteorologyAtmosphere
    ... publication_date=2000-09-01T00:00:00Z
    ... fees=None
    ... accessconstraints=otherRestrictions
    ... rights_en=Copyright (c) 2010 Her Majesty the Queen in Right of Canada
    ... rights_fr=Copyright (c) 2010 Her Majesty the Queen in Right of Canada
    ... url=http://geogratis.ca/geogratis/en/product/search.do?id=08DB5E85-7405-FE3A-2860-CC3663245625
    ... temporal_begin=1950-07-31
    ... temporal_end=now
    ... status=onGoing
    ... maintenancefrequency=continual
    ... 
    ... [contact:main]
    ... organization=Environment Canada
    ... url=http://www.ec.gc.ca/
    ... individualname=Tom Kralidis
    ... positionname=Senior Systems Scientist
    ... phone=+01-123-456-7890
    ... fax=+01-123-456-7890
    ... address=4905 Dufferin Street
    ... city=Toronto
    ... administrativearea=Ontario
    ... postalcode=M3H 5T4
    ... country=Canada
    ... email=foo@bar.tld
    ... hoursofservice=0700h - 1500h EST
    ... contactinstructions=email
    ... 
    ... [contact:distribution]
    ... #ref=contact:main
    ... organization=Environment Canada
    ... url=http://www.ec.gc.ca/
    ... individualname=Tom Kralidis
    ... positionname=Senior Systems Scientist
    ... phone=+01-123-456-7890
    ... fax=+01-123-456-7890
    ... address=4905 Dufferin Street
    ... city=Toronto
    ... administrativearea=Ontario
    ... postalcode=M3H 5T4
    ... country=Canada
    ... email=foo@bar.tld
    ... hoursofservice=0700h - 1500h EST
    ... contactinstructions=email
    ... 
    ... [distribution:waf]
    ... url=http://dd.meteo.gc.ca
    ... type=WWW:LINK
    ... name=my waf
    ... description_en=description in English
    ... description_fr=description in French
    ... function=download
    ... 
    ... [distribution:wms]
    ... url=http://dd.meteo.gc.ca
    ... type=OGC:WMS
    ... name_en=roads
    ... name_fr=routes
    ... description_en=description in English
    ... description_fr=description in French
    ... function=download'''
    >>> xml = _control_string_to_geographic_metadata(sample)
    >>> pprint(xml, width=78) # doctest: +ELLIPSIS
    ('<?xml version="1.0" ?>\\n'
     '<gmd:MD_Metadata xmlns:gco="http://www.isotc211.org/2005/gco" '
     'xmlns:gmd="http://www.isotc211.org/2005/gmd" '
     'xmlns:gml="http://www.opengis.net/gml/3.2" '
     'xmlns:gmx="http://www.isotc211.org/2005/gmx" '
     'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
     'xsi:schemaLocation="http://www.isotc211.org/2005/gmd '
     'http://www.isotc211.org/2005/gmd/gmd.xsd http://www.isotc211.org/2005/gmx '
     'http://www.isotc211.org/2005/gmx/gmx.xsd">\\n'
     '  <gmd:fileIdentifier>\\n'
     '    '
     '<gco:CharacterString>3f342f64-9348-11df-ba6a-0014c2c00eab</gco:CharacterString>\\n'
     '  </gmd:fileIdentifier>\\n'
     '  <gmd:language>\\n'
     '    <gmd:LanguageCode codeList="http://www.loc.gov/standards/iso639-2/" '
     'codeListValue="en" codeSpace="ISO 639-2">en</gmd:LanguageCode>\\n'
     '  </gmd:language>\\n'
     '  <gmd:characterSet>\\n'
     '    <gmd:MD_CharacterSetCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_CharacterSetCode" '
     'codeListValue="utf8" '
     'codeSpace="ISOTC211/19115">utf8</gmd:MD_CharacterSetCode>\\n'
     '  </gmd:characterSet>\\n'
     '  <gmd:parentIdentifier>\\n'
     '    <gco:CharacterString>someparentid</gco:CharacterString>\\n'
     '  </gmd:parentIdentifier>\\n'
     '  <gmd:hierarchyLevel>\\n'
     '    <gmd:MD_ScopeCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_ScopeCode" '
     'codeListValue="dataset" '
     'codeSpace="ISOTC211/19115">dataset</gmd:MD_ScopeCode>\\n'
     '  </gmd:hierarchyLevel>\\n'
     '  <gmd:contact>\\n'
     '    <gmd:CI_ResponsibleParty>\\n'
     '      <gmd:individualName>\\n'
     '        <gco:CharacterString>Tom Kralidis</gco:CharacterString>\\n'
     '      </gmd:individualName>\\n'
     '      <gmd:organisationName>\\n'
     '        <gco:CharacterString>Environment Canada</gco:CharacterString>\\n'
     '      </gmd:organisationName>\\n'
     '      <gmd:positionName>\\n'
     '        <gco:CharacterString>Senior Systems '
     'Scientist</gco:CharacterString>\\n'
     '      </gmd:positionName>\\n'
     '      <gmd:contactInfo>\\n'
     '        <gmd:CI_Contact>\\n'
     '          <gmd:phone>\\n'
     '            <gmd:CI_Telephone>\\n'
     '              <gmd:voice>\\n'
     '                '
     '<gco:CharacterString>+01-123-456-7890</gco:CharacterString>\\n'
     '              </gmd:voice>\\n'
     '              <gmd:facsimile>\\n'
     '                '
     '<gco:CharacterString>+01-123-456-7890</gco:CharacterString>\\n'
     '              </gmd:facsimile>\\n'
     '            </gmd:CI_Telephone>\\n'
     '          </gmd:phone>\\n'
     '          <gmd:address>\\n'
     '            <gmd:CI_Address>\\n'
     '              <gmd:deliveryPoint>\\n'
     '                <gco:CharacterString>4905 Dufferin '
     'Street</gco:CharacterString>\\n'
     '              </gmd:deliveryPoint>\\n'
     '              <gmd:city>\\n'
     '                <gco:CharacterString>Toronto</gco:CharacterString>\\n'
     '              </gmd:city>\\n'
     '              <gmd:administrativeArea>\\n'
     '                <gco:CharacterString>Ontario</gco:CharacterString>\\n'
     '              </gmd:administrativeArea>\\n'
     '              <gmd:postalCode>\\n'
     '                <gco:CharacterString>M3H 5T4</gco:CharacterString>\\n'
     '              </gmd:postalCode>\\n'
     '              <gmd:country>\\n'
     '                <gco:CharacterString>Canada</gco:CharacterString>\\n'
     '              </gmd:country>\\n'
     '              <gmd:electronicMailAddress>\\n'
     '                <gco:CharacterString>foo@bar.tld</gco:CharacterString>\\n'
     '              </gmd:electronicMailAddress>\\n'
     '            </gmd:CI_Address>\\n'
     '          </gmd:address>\\n'
     '          <gmd:onlineResource>\\n'
     '            <gmd:CI_OnlineResource>\\n'
     '              <gmd:linkage>\\n'
     '                <gmd:URL>http://www.ec.gc.ca/</gmd:URL>\\n'
     '              </gmd:linkage>\\n'
     '              <gmd:protocol>\\n'
     '                <gco:CharacterString>WWW:LINK</gco:CharacterString>\\n'
     '              </gmd:protocol>\\n'
     '            </gmd:CI_OnlineResource>\\n'
     '          </gmd:onlineResource>\\n'
     '          <gmd:hoursOfService>\\n'
     '            <gco:CharacterString>0700h - 1500h EST</gco:CharacterString>\\n'
     '          </gmd:hoursOfService>\\n'
     '          <gmd:contactInstructions>\\n'
     '            <gco:CharacterString>email</gco:CharacterString>\\n'
     '          </gmd:contactInstructions>\\n'
     '        </gmd:CI_Contact>\\n'
     '      </gmd:contactInfo>\\n'
     '      <gmd:role>\\n'
     '        <gmd:CI_RoleCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode" '
     'codeListValue="pointOfContact" '
     'codeSpace="ISOTC211/19115">pointOfContact</gmd:CI_RoleCode>\\n'
     '      </gmd:role>\\n'
     '    </gmd:CI_ResponsibleParty>\\n'
     '  </gmd:contact>\\n'
     '  <gmd:dateStamp>\\n'
     '    <gco:Date>2014-11-11</gco:Date>\\n'
     '  </gmd:dateStamp>\\n'
     '  <gmd:metadataStandardName>\\n'
     '    <gco:CharacterString>ISO 19115:2003 - Geographic information - '
     'Metadata</gco:CharacterString>\\n'
     '  </gmd:metadataStandardName>\\n'
     '  <gmd:metadataStandardVersion>\\n'
     '    <gco:CharacterString>ISO 19115:2003</gco:CharacterString>\\n'
     '  </gmd:metadataStandardVersion>\\n'
     '  <gmd:dataSetURI>\\n'
     '    <gco:CharacterString>http://some/minted/uri</gco:CharacterString>\\n'
     '  </gmd:dataSetURI>\\n'
     '  <gmd:locale>\\n'
     '    <gmd:PT_Locale id="locale-fr">\\n'
     '      <gmd:languageCode>\\n'
     '        <gmd:LanguageCode '
     'codeList="http://www.loc.gov/standards/iso639-2/" codeListValue="fr" '
     'codeSpace="ISO 639-2">fr</gmd:LanguageCode>\\n'
     '      </gmd:languageCode>\\n'
     '      <gmd:characterEncoding>\\n'
     '        <gmd:MD_CharacterSetCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_CharacterSetCode" '
     'codeListValue="utf8" '
     'codeSpace="ISOTC211/19115">utf8</gmd:MD_CharacterSetCode>\\n'
     '      </gmd:characterEncoding>\\n'
     '    </gmd:PT_Locale>\\n'
     '  </gmd:locale>\\n'
     '  <gmd:spatialRepresentationInfo>\\n'
     '    <gmd:MD_VectorSpatialRepresentation>\\n'
     '      <gmd:topologyLevel>\\n'
     '        <gmd:MD_TopologyLevelCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_TopologyLevelCode" '
     'codeListValue="geometryOnly" '
     'codeSpace="ISOTC211/19115">geometryOnly</gmd:MD_TopologyLevelCode>\\n'
     '      </gmd:topologyLevel>\\n'
     '      <gmd:geometricObjects>\\n'
     '        <gmd:MD_GeometricObjects>\\n'
     '          <gmd:geometricObjectType>\\n'
     '            <gmd:MD_GeometricObjectTypeCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_GeometricObjectTypeCode" '
     'codeListValue="point" '
     'codeSpace="ISOTC211/19115">point</gmd:MD_GeometricObjectTypeCode>\\n'
     '          </gmd:geometricObjectType>\\n'
     '        </gmd:MD_GeometricObjects>\\n'
     '      </gmd:geometricObjects>\\n'
     '    </gmd:MD_VectorSpatialRepresentation>\\n'
     '  </gmd:spatialRepresentationInfo>\\n'
     '  <gmd:referenceSystemInfo>\\n'
     '    <gmd:MD_ReferenceSystem>\\n'
     '      <gmd:referenceSystemIdentifier>\\n'
     '        <gmd:RS_Identifier>\\n'
     '          <gmd:authority>\\n'
     '            <gmd:CI_Citation>\\n'
     '              <gmd:title>\\n'
     '                <gco:CharacterString>European Petroleum Survey Group '
     '(EPSG) Geodetic Parameter Registry</gco:CharacterString>\\n'
     '              </gmd:title>\\n'
     '              <gmd:date>\\n'
     '                <gmd:CI_Date>\\n'
     '                  <gmd:date>\\n'
     '                    <gco:Date>2008-11-12</gco:Date>\\n'
     '                  </gmd:date>\\n'
     '                  <gmd:dateType>\\n'
     '                    <gmd:CI_DateTypeCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode" '
     'codeListValue="publication" '
     'codeSpace="ISOTC211/19115">publication</gmd:CI_DateTypeCode>\\n'
     '                  </gmd:dateType>\\n'
     '                </gmd:CI_Date>\\n'
     '              </gmd:date>\\n'
     '              <gmd:citedResponsibleParty>\\n'
     '                <gmd:CI_ResponsibleParty>\\n'
     '                  <gmd:organisationName>\\n'
     '                    <gco:CharacterString>European Petroleum Survey '
     'Group</gco:CharacterString>\\n'
     '                  </gmd:organisationName>\\n'
     '                  <gmd:contactInfo>\\n'
     '                    <gmd:CI_Contact>\\n'
     '                      <gmd:onlineResource>\\n'
     '                        <gmd:CI_OnlineResource>\\n'
     '                          <gmd:linkage>\\n'
     '                            '
     '<gmd:URL>http://www.epsg-registry.org</gmd:URL>\\n'
     '                          </gmd:linkage>\\n'
     '                        </gmd:CI_OnlineResource>\\n'
     '                      </gmd:onlineResource>\\n'
     '                    </gmd:CI_Contact>\\n'
     '                  </gmd:contactInfo>\\n'
     '                  <gmd:role>\\n'
     '                    <gmd:CI_RoleCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode" '
     'codeListValue="originator" '
     'codeSpace="ISOTC211/19115">originator</gmd:CI_RoleCode>\\n'
     '                  </gmd:role>\\n'
     '                </gmd:CI_ResponsibleParty>\\n'
     '              </gmd:citedResponsibleParty>\\n'
     '            </gmd:CI_Citation>\\n'
     '          </gmd:authority>\\n'
     '          <gmd:code>\\n'
     '            '
     '<gco:CharacterString>urn:ogc:def:crs:EPSG:4326</gco:CharacterString>\\n'
     '          </gmd:code>\\n'
     '          <gmd:version>\\n'
     '            <gco:CharacterString>6.18.3</gco:CharacterString>\\n'
     '          </gmd:version>\\n'
     '        </gmd:RS_Identifier>\\n'
     '      </gmd:referenceSystemIdentifier>\\n'
     '    </gmd:MD_ReferenceSystem>\\n'
     '  </gmd:referenceSystemInfo>\\n'
     '  <gmd:identificationInfo>\\n'
     '    <gmd:MD_DataIdentification>\\n'
     '      <gmd:citation>\\n'
     '        <gmd:CI_Citation>\\n'
     '          <gmd:title xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '            <gco:CharacterString>title in English</gco:CharacterString>\\n'
     '            <gmd:PT_FreeText>\\n'
     '              <gmd:textGroup>\\n'
     '                <gmd:LocalisedCharacterString locale="#locale-fr">title in '
     'French</gmd:LocalisedCharacterString>\\n'
     '              </gmd:textGroup>\\n'
     '            </gmd:PT_FreeText>\\n'
     '          </gmd:title>\\n'
     '          <gmd:date>\\n'
     '            <gmd:CI_Date>\\n'
     '              <gmd:date>\\n'
     '                <gco:DateTime>2000-09-01T00:00:00Z</gco:DateTime>\\n'
     '              </gmd:date>\\n'
     '              <gmd:dateType>\\n'
     '                <gmd:CI_DateTypeCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode" '
     'codeListValue="publication" '
     'codeSpace="ISOTC211/19115">publication</gmd:CI_DateTypeCode>\\n'
     '              </gmd:dateType>\\n'
     '            </gmd:CI_Date>\\n'
     '          </gmd:date>\\n'
     '        </gmd:CI_Citation>\\n'
     '      </gmd:citation>\\n'
     '      <gmd:abstract xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '        <gco:CharacterString>abstract in English</gco:CharacterString>\\n'
     '        <gmd:PT_FreeText>\\n'
     '          <gmd:textGroup>\\n'
     '            <gmd:LocalisedCharacterString locale="#locale-fr">abstract in '
     'French</gmd:LocalisedCharacterString>\\n'
     '          </gmd:textGroup>\\n'
     '        </gmd:PT_FreeText>\\n'
     '      </gmd:abstract>\\n'
     '      <gmd:status>\\n'
     '        <gmd:MD_ProgressCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_ProgressCode" '
     'codeListValue="onGoing" '
     'codeSpace="ISOTC211/19115">onGoing</gmd:MD_ProgressCode>\\n'
     '      </gmd:status>\\n'
     '      <gmd:resourceMaintenance>\\n'
     '        <gmd:MD_MaintenanceInformation>\\n'
     '          <gmd:maintenanceAndUpdateFrequency>\\n'
     '            <gmd:MD_MaintenanceFrequencyCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_MaintenanceFrequencyCode" '
     'codeListValue="continual" '
     'codeSpace="ISOTC211/19115">continual</gmd:MD_MaintenanceFrequencyCode>\\n'
     '          </gmd:maintenanceAndUpdateFrequency>\\n'
     '        </gmd:MD_MaintenanceInformation>\\n'
     '      </gmd:resourceMaintenance>\\n'
     '      <gmd:descriptiveKeywords>\\n'
     '        <gmd:MD_Keywords>\\n'
     '          <gmd:keyword xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '            <gco:CharacterString>kw1 in English</gco:CharacterString>\\n'
     '            <gmd:PT_FreeText>\\n'
     '              <gmd:textGroup>\\n'
     '                <gmd:LocalisedCharacterString locale="#locale-fr">kw1 in '
     'French</gmd:LocalisedCharacterString>\\n'
     '              </gmd:textGroup>\\n'
     '            </gmd:PT_FreeText>\\n'
     '          </gmd:keyword>\\n'
     '          <gmd:keyword xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '            <gco:CharacterString>kw2 in English</gco:CharacterString>\\n'
     '            <gmd:PT_FreeText>\\n'
     '              <gmd:textGroup>\\n'
     '                <gmd:LocalisedCharacterString locale="#locale-fr">kw2 in '
     'French</gmd:LocalisedCharacterString>\\n'
     '              </gmd:textGroup>\\n'
     '            </gmd:PT_FreeText>\\n'
     '          </gmd:keyword>\\n'
     '          <gmd:keyword xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '            <gco:CharacterString>kw3 in English</gco:CharacterString>\\n'
     '            <gmd:PT_FreeText>\\n'
     '              <gmd:textGroup>\\n'
     '                <gmd:LocalisedCharacterString locale="#locale-fr">kw3 in '
     'French</gmd:LocalisedCharacterString>\\n'
     '              </gmd:textGroup>\\n'
     '            </gmd:PT_FreeText>\\n'
     '          </gmd:keyword>\\n'
     '          <gmd:type>\\n'
     '            <gmd:MD_KeywordTypeCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_KeywordTypeCode" '
     'codeListValue="theme" '
     'codeSpace="ISOTC211/19115">theme</gmd:MD_KeywordTypeCode>\\n'
     '          </gmd:type>\\n'
     '        </gmd:MD_Keywords>\\n'
     '      </gmd:descriptiveKeywords>\\n'
     '      <gmd:resourceConstraints>\\n'
     '        <gmd:MD_LegalConstraints>\\n'
     '          <gmd:accessConstraints>\\n'
     '            <gmd:MD_RestrictionCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_RestrictionCode" '
     'codeListValue="otherRestrictions" '
     'codeSpace="ISOTC211/19115">otherRestrictions</gmd:MD_RestrictionCode>\\n'
     '          </gmd:accessConstraints>\\n'
     '        </gmd:MD_LegalConstraints>\\n'
     '      </gmd:resourceConstraints>\\n'
     '      <gmd:spatialRepresentationType>\\n'
     '        <gmd:MD_SpatialRepresentationTypeCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_SpatialRepresentationTypeCode" '
     'codeListValue="vector" '
     'codeSpace="ISOTC211/19115">vector</gmd:MD_SpatialRepresentationTypeCode>\\n'
     '      </gmd:spatialRepresentationType>\\n'
     '      <gmd:language>\\n'
     '        <gco:CharacterString>eng; CAN</gco:CharacterString>\\n'
     '      </gmd:language>\\n'
     '      <gmd:characterSet>\\n'
     '        <gmd:MD_CharacterSetCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_CharacterSetCode" '
     'codeListValue="utf8" '
     'codeSpace="ISOTC211/19115">utf8</gmd:MD_CharacterSetCode>\\n'
     '      </gmd:characterSet>\\n'
     '      <gmd:topicCategory>\\n'
     '        '
     '<gmd:MD_TopicCategoryCode>climatologyMeteorologyAtmosphere</gmd:MD_TopicCategoryCode>\\n'
     '      </gmd:topicCategory>\\n'
     '      <gmd:extent>\\n'
     '        <gmd:EX_Extent>\\n'
     '          <gmd:geographicElement>\\n'
     '            <gmd:EX_GeographicBoundingBox>\\n'
     '              <gmd:extentTypeCode>\\n'
     '                <gco:Boolean>1</gco:Boolean>\\n'
     '              </gmd:extentTypeCode>\\n'
     '              <gmd:westBoundLongitude>\\n'
     '                <gco:Decimal>-141</gco:Decimal>\\n'
     '              </gmd:westBoundLongitude>\\n'
     '              <gmd:eastBoundLongitude>\\n'
     '                <gco:Decimal>-52</gco:Decimal>\\n'
     '              </gmd:eastBoundLongitude>\\n'
     '              <gmd:southBoundLatitude>\\n'
     '                <gco:Decimal>42</gco:Decimal>\\n'
     '              </gmd:southBoundLatitude>\\n'
     '              <gmd:northBoundLatitude>\\n'
     '                <gco:Decimal>84</gco:Decimal>\\n'
     '              </gmd:northBoundLatitude>\\n'
     '            </gmd:EX_GeographicBoundingBox>\\n'
     '          </gmd:geographicElement>\\n'
     '          <gmd:temporalElement>\\n'
     '            <gmd:EX_TemporalExtent>\\n'
     '              <gmd:extent>\\n'
     '                <gml:TimePeriod gml:id="T001">\\n'
     '                  <gml:beginPosition>1950-07-31</gml:beginPosition>\\n'
     '                  <gml:endPosition indeterminatePosition="now"/>\\n'
     '                </gml:TimePeriod>\\n'
     '              </gmd:extent>\\n'
     '            </gmd:EX_TemporalExtent>\\n'
     '          </gmd:temporalElement>\\n'
     '        </gmd:EX_Extent>\\n'
     '      </gmd:extent>\\n'
     '      <gmd:supplementalInformation>\\n'
     '        '
     '<gco:CharacterString>http://geogratis.ca/geogratis/en/product/search.do?id=08DB5E85-7405-FE3A-2860-CC3663245625</gco:CharacterString>\\n'
     '      </gmd:supplementalInformation>\\n'
     '    </gmd:MD_DataIdentification>\\n'
     '  </gmd:identificationInfo>\\n'
     '  <gmd:distributionInfo>\\n'
     '    <gmd:MD_Distribution>\\n'
     '      <gmd:distributor>\\n'
     '        <gmd:MD_Distributor>\\n'
     '          <gmd:distributorContact>\\n'
     '            <gmd:CI_ResponsibleParty>\\n'
     '              <gmd:individualName>\\n'
     '                <gco:CharacterString>Tom Kralidis</gco:CharacterString>\\n'
     '              </gmd:individualName>\\n'
     '              <gmd:organisationName>\\n'
     '                <gco:CharacterString>Environment '
     'Canada</gco:CharacterString>\\n'
     '              </gmd:organisationName>\\n'
     '              <gmd:positionName>\\n'
     '                <gco:CharacterString>Senior Systems '
     'Scientist</gco:CharacterString>\\n'
     '              </gmd:positionName>\\n'
     '              <gmd:contactInfo>\\n'
     '                <gmd:CI_Contact>\\n'
     '                  <gmd:phone>\\n'
     '                    <gmd:CI_Telephone>\\n'
     '                      <gmd:voice>\\n'
     '                        '
     '<gco:CharacterString>+01-123-456-7890</gco:CharacterString>\\n'
     '                      </gmd:voice>\\n'
     '                      <gmd:facsimile>\\n'
     '                        '
     '<gco:CharacterString>+01-123-456-7890</gco:CharacterString>\\n'
     '                      </gmd:facsimile>\\n'
     '                    </gmd:CI_Telephone>\\n'
     '                  </gmd:phone>\\n'
     '                  <gmd:address>\\n'
     '                    <gmd:CI_Address>\\n'
     '                      <gmd:deliveryPoint>\\n'
     '                        <gco:CharacterString>4905 Dufferin '
     'Street</gco:CharacterString>\\n'
     '                      </gmd:deliveryPoint>\\n'
     '                      <gmd:city>\\n'
     '                        '
     '<gco:CharacterString>Toronto</gco:CharacterString>\\n'
     '                      </gmd:city>\\n'
     '                      <gmd:administrativeArea>\\n'
     '                        '
     '<gco:CharacterString>Ontario</gco:CharacterString>\\n'
     '                      </gmd:administrativeArea>\\n'
     '                      <gmd:postalCode>\\n'
     '                        <gco:CharacterString>M3H '
     '5T4</gco:CharacterString>\\n'
     '                      </gmd:postalCode>\\n'
     '                      <gmd:country>\\n'
     '                        <gco:CharacterString>Canada</gco:CharacterString>\\n'
     '                      </gmd:country>\\n'
     '                      <gmd:electronicMailAddress>\\n'
     '                        '
     '<gco:CharacterString>foo@bar.tld</gco:CharacterString>\\n'
     '                      </gmd:electronicMailAddress>\\n'
     '                    </gmd:CI_Address>\\n'
     '                  </gmd:address>\\n'
     '                  <gmd:onlineResource>\\n'
     '                    <gmd:CI_OnlineResource>\\n'
     '                      <gmd:linkage>\\n'
     '                        <gmd:URL>http://www.ec.gc.ca/</gmd:URL>\\n'
     '                      </gmd:linkage>\\n'
     '                      <gmd:protocol>\\n'
     '                        '
     '<gco:CharacterString>WWW:LINK</gco:CharacterString>\\n'
     '                      </gmd:protocol>\\n'
     '                    </gmd:CI_OnlineResource>\\n'
     '                  </gmd:onlineResource>\\n'
     '                  <gmd:hoursOfService>\\n'
     '                    <gco:CharacterString>0700h - 1500h '
     'EST</gco:CharacterString>\\n'
     '                  </gmd:hoursOfService>\\n'
     '                  <gmd:contactInstructions>\\n'
     '                    <gco:CharacterString>email</gco:CharacterString>\\n'
     '                  </gmd:contactInstructions>\\n'
     '                </gmd:CI_Contact>\\n'
     '              </gmd:contactInfo>\\n'
     '              <gmd:role>\\n'
     '                <gmd:CI_RoleCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode" '
     'codeListValue="distributor" '
     'codeSpace="ISOTC211/19115">distributor</gmd:CI_RoleCode>\\n'
     '              </gmd:role>\\n'
     '            </gmd:CI_ResponsibleParty>\\n'
     '          </gmd:distributorContact>\\n'
     '        </gmd:MD_Distributor>\\n'
     '      </gmd:distributor>\\n'
     '      <gmd:transferOptions>\\n'
     '        <gmd:MD_DigitalTransferOptions>\\n'
     '          <gmd:onLine>\\n'
     '            <gmd:CI_OnlineResource>\\n'
     '              <gmd:linkage>\\n'
     '                <gmd:URL>http://dd.meteo.gc.ca</gmd:URL>\\n'
     '              </gmd:linkage>\\n'
     '              <gmd:protocol>\\n'
     '                <gco:CharacterString>WWW:LINK</gco:CharacterString>\\n'
     '              </gmd:protocol>\\n'
     '              <gmd:name>\\n'
     '                <gco:CharacterString>my waf</gco:CharacterString>\\n'
     '              </gmd:name>\\n'
     '              <gmd:description xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '                <gco:CharacterString>description in '
     'English</gco:CharacterString>\\n'
     '                <gmd:PT_FreeText>\\n'
     '                  <gmd:textGroup>\\n'
     '                    <gmd:LocalisedCharacterString '
     'locale="#locale-fr">description in French</gmd:LocalisedCharacterString>\\n'
     '                  </gmd:textGroup>\\n'
     '                </gmd:PT_FreeText>\\n'
     '              </gmd:description>\\n'
     '              <gmd:function>\\n'
     '                <gmd:CI_OnLineFunctionCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_OnLineFunctionCode" '
     'codeListValue="download" '
     'codeSpace="ISOTC211/19115">download</gmd:CI_OnLineFunctionCode>\\n'
     '              </gmd:function>\\n'
     '            </gmd:CI_OnlineResource>\\n'
     '          </gmd:onLine>\\n'
     '          <gmd:onLine>\\n'
     '            <gmd:CI_OnlineResource>\\n'
     '              <gmd:linkage>\\n'
     '                <gmd:URL>http://dd.meteo.gc.ca</gmd:URL>\\n'
     '              </gmd:linkage>\\n'
     '              <gmd:protocol>\\n'
     '                <gco:CharacterString>OGC:WMS</gco:CharacterString>\\n'
     '              </gmd:protocol>\\n'
     '              <gmd:name xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '                <gco:CharacterString>roads</gco:CharacterString>\\n'
     '                <gmd:PT_FreeText>\\n'
     '                  <gmd:textGroup>\\n'
     '                    <gmd:LocalisedCharacterString '
     'locale="#locale-fr">routes</gmd:LocalisedCharacterString>\\n'
     '                  </gmd:textGroup>\\n'
     '                </gmd:PT_FreeText>\\n'
     '              </gmd:name>\\n'
     '              <gmd:description xsi:type="gmd:PT_FreeText_PropertyType">\\n'
     '                <gco:CharacterString>description in '
     'English</gco:CharacterString>\\n'
     '                <gmd:PT_FreeText>\\n'
     '                  <gmd:textGroup>\\n'
     '                    <gmd:LocalisedCharacterString '
     'locale="#locale-fr">description in French</gmd:LocalisedCharacterString>\\n'
     '                  </gmd:textGroup>\\n'
     '                </gmd:PT_FreeText>\\n'
     '              </gmd:description>\\n'
     '              <gmd:function>\\n'
     '                <gmd:CI_OnLineFunctionCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_OnLineFunctionCode" '
     'codeListValue="download" '
     'codeSpace="ISOTC211/19115">download</gmd:CI_OnLineFunctionCode>\\n'
     '              </gmd:function>\\n'
     '            </gmd:CI_OnlineResource>\\n'
     '          </gmd:onLine>\\n'
     '        </gmd:MD_DigitalTransferOptions>\\n'
     '      </gmd:transferOptions>\\n'
     '    </gmd:MD_Distribution>\\n'
     '  </gmd:distributionInfo>\\n'
     '  <gmd:metadataMaintenance>\\n'
     '    <gmd:MD_MaintenanceInformation>\\n'
     '      <gmd:maintenanceAndUpdateFrequency>\\n'
     '        <gmd:MD_MaintenanceFrequencyCode '
     'codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_MaintenanceFrequencyCode" '
     'codeListValue="continual" '
     'codeSpace="ISOTC211/19115">continual</gmd:MD_MaintenanceFrequencyCode>\\n'
     '      </gmd:maintenanceAndUpdateFrequency>\\n'
     '      <gmd:maintenanceNote>\\n'
     '        <gco:CharacterString>This metadata record was generated by '
     'pygeometa-... '
     '(https://github.com/geopython/pygeometa)</gco:CharacterString>\\n'
     '      </gmd:maintenanceNote>\\n'
     '    </gmd:MD_MaintenanceInformation>\\n'
     '  </gmd:metadataMaintenance>\\n'
     '</gmd:MD_Metadata>')
    """
    iso19139_jinja_dir = os.path.dirname(__file__) # Jinja2 templates to
        # generate WCODP-compliant Geographic MetaData (GMD) XML are stored in
        # the same directory as this Python module.
    with NamedTemporaryFile() as fp:
        fp.write(metadata_control.encode('utf-8'))
        fp.seek(0) #reset file-pointer, for reading
        temp_file_name = fp.name
        xml = render_template(temp_file_name, schema_local=iso19139_jinja_dir)
    return xml
