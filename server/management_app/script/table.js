$(document).ready(function() {
    $('#tables').DataTable( {
        "ajax": {
            "url": '../management_api/v1/dump/json',
            "dataSrc": 'model.tables'
        },
        "columns": [
            { data: "name" },
            { data: "project" },
            { data: "type" },
            { data: "title" },
            { data: "years" },
            { data: "selectable" },
            { data: "confidential" },
            //{ data: "uuid" },
            { data: "inport_replacement_project_id" },
            { data: "inport_id" }
        ]
    } );
} );
