# FRAM Data Warehouse - Management API

To configure data warehouse, direct your web client to the Management API server/port combination specified by the `management.proxy_url_base` setting in the  `server/server.ini` API installation file. Example:
```
http://mydatahost.example:8080/management_api/v1/p3p
```

## Access
Managment actions are only available to logged in users with a valid "api.session.id" cookie set by the Warehouse Client API. Access is further restricted to users who's login ID is authorized for warehouse management, via the `dwsupport.management_authorization` database table.

## Overview
Available API features:
* [/dump - Export configuration](#export-configuration)
* [/table/{id}/copy - Add new table](#add-table)
* [/table/{id}/variables - Table variables](#table-variables)
* [/help - API Documentation](#api-documentation)
* [/p3p - Privacy Information](#privacy-information)

## Export configuration

The full warehouse configuration may be exported as a Python module via any of the URIs:
```
management_api/v1/dump
management_api/v1/dump/
management_api/v1/dump/{format}
```

#### Supported Output Formats
* py -- Python module, defining a `model` configuration dictionary
* json -- JavaScript Object Notation text [ECMA-404 JSON Data Interchange Standard](http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf)

## Add Table
Creating new DWSupport table entries via copy, is available through HTTP POST. To specify which table to copy, substitute the _id_ of the desired source into the URI:
```
management_api/v1/table/{id}/copy
```

All related table details (including: Variables, Associations, Customized Variable Identifiers, & Queries) will also be copied & assigned to the new table.

#### HTTP POST Parameters
* table  -- (Required) String, representing name for the new Table
* project-name  -- (Required) String, representing project new Table will belong to 
* variable-custom-identifiers  -- (Required) JSON Object, representing new unique names for the existing table variable customized identifiers.
    ```
// example of an empty 'variable-custom-identifiers' Object (for copying Table with no customized fields)
{}

// example Object, for copying a Table with 2x custom IDs
{"custom_variable_on_existing_table": "my_new_customized_variable_identifier",
 "another_custom_variable_on_table": "my_other_customized_variable_identifier"}
    ```

#### Supported Table Types
Currently only one type of table may be copied:
* fact  -- DWSupport fact tables (view or physical table)


## Table Variables
A list of all DWSupport variables for a specified table, can be obtained by specifying _id_ of the desired source table into the URI:
```
management_api/v1/table/{id}/variables
```

In addition to DWSupport.variable details, each returned `variable` is paired with its corresponding `variable_custom_identifier`, `queries`, and (if variable is physically part of a different table) source table `association_column`.

### Alter Variables
A variable for a new physical database column may be added, or one existing variable's Query modified, through HTTP POST of [DataTables Editor style](https://editor.datatables.net/manual/server#Client-to-server) parameters to the above [table variable URL](#manage-table-variables).

#### Variable Add - HTTP POST Parameters
* action  -- (Required) String, value must be set to: `create`
* data[0][table]  -- (Required) String, representing name of DWSupport Table variable physically belongs to
* data[0][column]  -- (Required) String, representing variable's physical column name
* data[0][title]  -- (Required) String, representing project new Table will belong to 
* data[0][python_type]  -- (Required) String, representing python type of the field (one of 'str', 'int', or 'float')
* data[0][defaults]  -- (Optional) String, representing a comma-separated list of Queries variable will belong to

#### Variable Query Update - HTTP POST Parameters
* data[{table}.{column}][column]  -- (Required) String, representing variable's physical column name
* data[{table}.{column}][defaults]  -- (Required) String, representing a comma-separated list of Queries variable will belong to

 1. To update, `{table}` and `{column}` in HTTP POST parameter names must be substituted with the current, physical table name & column name of the variable being modified. That is, the names of POST parameters will be different for each distinct variable; This is a function that the DataTables Editor client JavaScript does automatically.


## API Documentation

The current version of this documentation (HTML-formatted) may be obtained via URI:
```
management_api/v1/help
```

## Privacy Information

A machine-readable P3P ([Platform for Privacy Preferences](https://www.w3.org/P3P/)) Policy Reference File may be obtained via URI:
```
management_api/v1/p3p.xml
```

### Privacy Information Header
Machine-readable privacy reference information is also available with every API response, via HTTP header: P3P

#### Copyright 2017 ERT, inc. All Rights reserved
