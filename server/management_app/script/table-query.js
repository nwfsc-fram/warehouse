var editor;

/** DataTables utility, returning array of objects for table
 */
function getQueriesDataSrc(json_columns) {
    // get data warehouse model
    if (typeof json_columns == 'object') {
        var columns = json_columns.variables;
    } else { //DataTables Editor passes JSON, not an object
        var columns = JSON.parse(json_columns).variables;
    }
    var data = [];
    for (var column of columns) {
        // add row
        var row = {
            "DT_RowId": column.variable.table + "." + column.variable.column,
            "association": column.association_column,
            "table": column.variable.table,
            "column": column.variable.column,
            "title": column.variable.title,
            "python_type": column.variable.python_type,
            "alias": column.variable_custom_identifier,
            "defaults": column.queries
        };
        data.push(row);
    };
    return data;
};

$(document).ready(function() {
    editor = new $.fn.dataTable.Editor( {
        "ajax": {
            "url": '../management_api/v1/table/&#46;/variables',
            "dataSrc": getQueriesDataSrc,
            "error": function(xhr, error, thrown){
                //redirect errors, though HTTP 200 handler
                //per: https://datatables.net/forums/discussion/32279/ajax-handling-status-code-400-for-invalid-new-record
                var response_object = JSON.parse(xhr.responseText)
                var force_status = 200
                this.success(response_object, force_status, xhr);
            }
        },
        table: "#queries",
        fields: [{
                label: "Association:",
                name: "association"
            },{
                label: "Table:",
                name: "table"
            },
            {
                label: "Column:",
                name: "column"
            },
            {
                label: "Title:",
                name: "title"
            },
            {
                label: "Python Type:",
                name: "python_type"
            }, {
                label: "Alias:",
                name: "alias"
            }, {
                label: "Defaults:",
                name: "defaults"
            }
        ]
    } );

    $('#queries').DataTable( {
        dom: 'Bfrtip',
        "ajax": {
            "url": '../management_api/v1/table/&#46;/variables',
            "dataSrc": getQueriesDataSrc
        },
        "columns": [
            { data: "association" },
            { data: "table" },
            { data: "column" },
            { data: "title" },
            { data: "alias" },
            { data: "defaults" }
        ],
        select: true,
        buttons: [
            { extend: "edit",   editor: editor },
            { extend: "create",   editor: editor }
        ]
    } );
} );
