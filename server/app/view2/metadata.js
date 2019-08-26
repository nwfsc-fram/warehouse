'use strict';

angular.module('myApp.metadata', ['ngRoute'])

.controller('MetadataCtrl', ['$scope','$http', '$routeParams',function($scope,$http, $routeParams) {


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
	Metadata retrieval functionality
**********************************************************************************************************************************************/


    $scope.layer = $routeParams.layer;
    $scope.project;
    $scope.description;
    $scope.yearsOfData;
    $scope.pointOfContact;
    $scope.lastUpdated;

    $scope.showLayer = false;

	$http.get(api_base_uri).success(function(json)
	{

        var data = json.sources;
		var i=0;

        for (var i = 0; i < data.length; i++) {
            if($scope.layer==data[i].id)
            {
                $scope.layer = data[i].title;
                $scope.project = data[i].project;
                $scope.description = data[i].description;
                $scope.yearsOfData = data[i].years;
                $scope.pointOfContact = data[i].contact.replace("<","").replace(">","");

                if (data[i].links.length>2)
                {
                    $scope.json_url = data[i].links[1].href;
                    $scope.csv_url = data[i].links[0].href;
                    if ($scope.layer === 'GEMM Fact') {
                        $scope.xslx_url = data[i].links[2].href;
                    }
                }

                var lastDateUpdated = new Date(data[i].updated);
                $scope.lastUpdated = (lastDateUpdated.getMonth() + 1) +'/'+ lastDateUpdated.getDate() +'/'+ lastDateUpdated.getFullYear()
                        +' '+lastDateUpdated.getHours()+':'+lastDateUpdated.getMinutes() +':'+lastDateUpdated.getSeconds();

                $scope.showLayer = true;
             }
        }

	});



//    console.log(api_base_uri+$routeParams.layer+'/variables');
  $('#metadata').DataTable( {
       "processing": true,
       "autoWidth": false,
       "ajax": {
            "url": api_base_uri+$routeParams.layer+'/variables',
            "dataSrc": "variables"
        },
        "columns": [

                { "data": "title", title: 'Title',"width": "20%", defaultContent: "" },
                { "data": "description", title: 'Description', defaultContent: "" },
                { "data": "type", title: 'Type', defaultContent: "" },
                { "data": "max_length", title: 'Max Length', defaultContent: "" },
                { "data": "precision", title: 'Precision', defaultContent: "" },
                { "data": "units", title: 'Units', defaultContent: "" },
                { "data": "allowed_values", title: 'Allowed Values', defaultContent: "" },
                { "data": "id", title: 'ID', defaultContent: "" }


            ],
            "pagingType": "full_numbers"
    } );


}]) //end Login 