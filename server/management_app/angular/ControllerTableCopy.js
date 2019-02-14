'use strict';
/*AngularJS module, defining a controller for Warehouse table copying
 *
 * table is copied via AJAX call, as specified by URL Query path & HTML
 *   POST parameters
 *
 * Copyright (C) 2017 ERT Inc.
*/
angular.module('tableApp', [])
    .controller('TableCopyFormController', ['$scope', function($scope) {
      $scope.action = "../management_api/v1/table/&#46;/copy";

      $scope.submit = function() {
        $scope.action = "../management_api/v1/table/"+$scope.project+"."+$scope.table+"/copy";
      };

    }]);
