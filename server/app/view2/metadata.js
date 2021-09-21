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
	Metadata retrieval functionality
**********************************************************************************************************************************************/


    $scope.layer = $routeParams.layer;
    $scope.project;
    $scope.description;
    $scope.yearsOfData;
    $scope.pointOfContact;
    $scope.lastUpdated;

    $scope.showLayer = false;
    $scope.showGEMM = false;

	$http.get(api_base_uri).success(function(json)
	{
        var urlJSON = "";
        var urlCSV = "";
        var urlXLSX = "";


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
                    urlCSV = data[i].links[0].href;//.replace("https://","https://www.");
                    urlJSON = json.sources[i].links[1].href;//.replace("https://","https://www.");
                    urlXLSX = json.sources[i].links[2].href;//.replace("https://","https://www.");
                    
                    if (env='PROD')
                    {
                        urlCSV = urlCSV.replace("nwfsc","webapps.nwfsc");
                        urlJSON = urlJSON.replace("nwfsc","webapps.nwfsc");
                        urlXLSX = urlXLSX.replace("nwfsc","webapps.nwfsc");
                    }
                    
                    $scope.json_url = urlJSON;
                    $scope.csv_url = urlCSV;
                    if ($scope.layer === 'GEMM Fact') {
                        $scope.xlsx_url = urlXLSX;
                    }
                }

                var lastDateUpdated = new Date(data[i].updated);
                $scope.lastUpdated = (lastDateUpdated.getMonth() + 1) +'/'+ lastDateUpdated.getDate() +'/'+ lastDateUpdated.getFullYear()
                        +' '+lastDateUpdated.getHours()+':'+lastDateUpdated.getMinutes() +':'+lastDateUpdated.getSeconds();

                if ($scope.layer != 'GEMM Fact')
                    $scope.showLayer = true; 
                else
                    $scope.showGEMM = true;
                
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