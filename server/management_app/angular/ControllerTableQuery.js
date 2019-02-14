'use strict';
/*AngularJS module, defining a controller for Warehouse table copying
 *
 * table is copied via AJAX call, as specified by URL Query path & HTML
 *   POST parameters
 *
 * Copyright (C) 2017 ERT Inc.
*/
angular.module('queryApp', [])
    .controller('SourceFormController', ['$scope', function($scope) {

      $scope.submit = function() {
        $('#queries').DataTable().ajax.url(
        "../management_api/v1/table/"+$scope.project+"."+$scope.table+"/variables").load();
        editor.s.ajax.url = "../management_api/v1/table/"+$scope.project+"."+$scope.table+"/variables";
      };

    }]);
