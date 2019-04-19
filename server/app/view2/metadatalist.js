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

	if(api_base_uri.indexOf("nwcdevfram")>=0 || api_base_uri.indexOf("localhost")>=0)
		api_base_uri = 'https://nwcdevfram.nwfsc.noaa.gov/api/v1/source/';
	else if(api_base_uri.indexOf("devwww11")>=0)
		api_base_uri = 'https://devwww11.nwfsc.noaa.gov/data/api/v1/source/';
	else
		api_base_uri = 'https://www.nwfsc.noaa.gov/data/api/v1/source/';

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

              for ( var i=0, ien=json.sources.length ; i<ien ; i++ )
                  if ((json.sources[i].name.includes("fact") || json.sources[i].name.includes("view")) && !json.sources[i].project.includes("edc") ) {
                      json.sources[i].updated = moment.tz(json.sources[i].updated, "America/Los_Angeles").format('MM/DD/YYYY HH:mm:ss');
                      json.sources[i].download_links = '<a href=" '+ json.sources[i].links[0].href +' " target="_blank">CSV</a>, <a href="' + json.sources[i].links[1].href + '" target="_blank">JSON</a>';
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
