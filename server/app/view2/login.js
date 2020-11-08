'use strict';

angular.module('myApp.login', ['ngRoute','ngMaterial','angular-loading-bar','ngSanitize','ngCookies'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/login', {
    templateUrl: 'view2/login.html'
  });

}])


.controller('LoginCtrl', ['$scope','$http', '$timeout', '$mdSidenav', '$mdUtil', '$log','$q', '$mdDialog', '$mdMedia','$cookies',function($scope,$http, $timeout, $mdSidenav, $mdUtil, $log, $q,  $mdDialog, $mdMedia, $cookies) {


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
        api_base_uri = 'https://www.devwebapps.nwfsc.noaa.gov/data';    
        env = 'DEV';
    }
	else if(api_base_uri.indexOf("webapps.nwfsc.noaa.gov")>=0 )
		api_base_uri = 'https://www.webapps.nwfsc.noaa.gov/data';
	else
        api_base_uri = 'https://www.nwfsc.noaa.gov/data';

/*********************************************************************************************************************************************
	Login functionality
**********************************************************************************************************************************************/

	  
console.log( "cookies=");

	console.log( $cookies.get('api.session.id'));

     $scope.login = function () {
           // use $.param jQuery function to serialize data from JSON 
            var data = $.param({
                username: $scope.username,
                password: $scope.password
            });
        
           var config = {
                headers : {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'
                }
            }

            $http.post(api_base_uri+'/api/v1/login', data, config)
            .success(function (data, status, headers, config) {
				console.log("in success");
				$scope.loginError = "";
                $scope.loginSuccess =  "Logged in successfully";

	console.log( $cookies.get('api.session.id'));
            })
            .error(function (data, status, header, config) {

					console.log("in error");
           $scope.loginSuccess = "";
                $scope.loginError =  data.title + ": "+ data.description;

	
            });
			
        };


}]) //end Login 