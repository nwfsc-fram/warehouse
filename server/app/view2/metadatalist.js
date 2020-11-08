angular.module('myApp.metadatalist', ['ngRoute'])

.controller('MetadataListCtrl', ['$scope','$http', '$routeParams',function($scope,$http, $routeParams) {


/*********************************************************************************************************************************************
	API URL path setup
**********************************************************************************************************************************************/


	//get the URL absolute path
	function getAbsolutePath() {
		var loc = window.location;
		var pathName = loc.pathname.substring(0, loc.pathname.lastIndexOf('/') + 1);
		return loc.href.substring(0, loc.href.length - ((loc.pathname + loc.search + loc.hash).length - pathName.length));
	}

    var api_base_uri = getAbsolutePath();
    var env = 'PROD';

	if(api_base_uri.indexOf("devwebapps")>=0 || api_base_uri.indexOf("localhost")>=0)
    {
        api_base_uri = 'https://www.devwebapps.nwfsc.noaa.gov/data/api/v1/source/';    
        env = 'DEV';
    }
	else if(api_base_uri.indexOf("webapps.nwfsc.noaa.gov")>=0 )
		api_base_uri = 'https://www.webapps.nwfsc.noaa.gov/data/api/v1/source/';
	else
        api_base_uri = 'https://www.nwfsc.noaa.gov/data/api/v1/source/';
            
		console.log("api_base_uri is");

		console.log(api_base_uri);

/*********************************************************************************************************************************************
	Metadata list retrieval functionality
**********************************************************************************************************************************************/

  $('#metadatalist').DataTable( {
      "processing": true,
      "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
      "pageLength": -1,
       "ajax": {
           "url": api_base_uri,
           "dataSrc": function ( json ) {
              var metadataList=[];
              var urlJSON = "";
              var urlCSV = "";
              var urlXLSX = "";
              for ( var i=0, ien=json.sources.length ; i<ien ; i++ )

                if ((json.sources[i].name.includes("fact") || json.sources[i].name.includes("view")) && !json.sources[i].project.includes("edc") ) {
                    json.sources[i].updated = moment.tz(json.sources[i].updated, "America/Los_Angeles").format('MM/DD/YYYY HH:mm:ss');
                    urlCSV = json.sources[i].links[0].href;
                    urlJSON = json.sources[i].links[1].href;
                    urlXLSX = json.sources[i].links[2].href;
                    
                    if (env=='PROD')
                    {
                        urlCSV = urlCSV.replace("nwfsc","webapps.nwfsc");
                        urlJSON = urlJSON.replace("nwfsc","webapps.nwfsc");
                        urlXLSX = urlXLSX.replace("nwfsc","webapps.nwfsc");
                    }
                    else
                    {
                        urlCSV = urlCSV.replace("devwebapps.","www.devwebapps.");
                        urlJSON = urlJSON.replace("devwebapps.","www.devwebapps.");
                        urlXLSX = urlXLSX.replace("devwebapps.","www.devwebapps.");
                    }

                    if (json.sources[i].name === "gemm_fact") {
                        json.sources[i].download_links = '<a href=" '+urlCSV +' " target="_blank">CSV</a>, <a href="' + urlJSON + '" target="_blank">JSON</a>, <a href="' + urlXLSX + '" target="_blank">XLSX</a>';
                    } else {
                      json.sources[i].download_links = '<a href=" '+urlCSV +' " target="_blank">CSV</a>, <a href="' +  urlJSON + '" target="_blank">JSON</a>';
                    }
                      metadataList.push(json.sources[i]);
                  }
              return metadataList;
            }
        },
        "columns": [

                { "data": "project", title: 'Project', defaultContent: "" },
                { "data": "name", title: 'Layer', defaultContent: "",
                    "render": function ( data, type, row, meta )
                        {
                            return '<a href="metadata/'+row.project+'.'+data+'">'+data+'</a>';
                        }
                    },
                { "data": "description", title: 'Description', defaultContent: "" },
                { "data": "years", title: 'Years of Data',"width": "105px",  defaultContent: "" },
                { "data": "download_links", title: 'Download Data', "width": "130px",defaultContent: "" },
                { "data": "updated", title: 'Updated', "width": "165px",defaultContent: "" }

            ],
            "pagingType": "full_numbers"
    } );

    $scope.contactDisplay = false

    $scope.displayDialog = function() {
        $scope.contactDisplay = $scope.contactDisplay ? false : true;
    }    

    $scope.closeDialog = function() {
        $scope.contactDisplay = false
    }


}]) //end Login

'use strict';
