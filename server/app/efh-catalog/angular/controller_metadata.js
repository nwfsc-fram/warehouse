'use strict';
/*AngularJS module, defining a controller for EFH-Catalog item metadata display
 *
 * EFH-Catalog item is specified via URL Query parameters & fetched via AJAX
 *
 * Copyright (C) 2016 ERT Inc.
*/
angular.module('efhMetadata', ['ngSanitize'])
  .config(function($locationProvider) {
    // use the HTML5 History API
    $locationProvider.html5Mode({
      enabled: true,
      requireBase: false
    });
  })
  .controller('efhMetadataTableController', ['$location', '$http', function($location, $http) {
    var tableController = this; //reference, to this AngularJS controller
    var api_base = "http://NwcDevFRAM.nwfsc.noaa.gov"
    var catalog_id = "efh.efh_catalog_fact"

    // place an initial loading message
    tableController.model = {
      ref: "Loading Metadata ..."
    };

    // fetch metadata
    var urlQueryString = $location.search();
    $http({
      method: 'GET',
      url: api_base+'/api/v1/source/'+catalog_id+'/selection.json'
    }).then(function successCallback(response) {
      // API responded. Update the HTML table
      update(response);
    }, function errorCallback(response) {
      // API failure! place an error message
      tableController.model = {
        ref: 'Metadata loading error. Please try again ('+$location.absUrl()+') or contact "'
             + catalog_id+'" maintainer listed on '+api_base+'/api/v1/source for assistance'
      };
    });

    function update(response) {
      // locate the requested catalog item
      var catalog = response.data;
      var catalog_row_requested = urlQueryString['catalog_row_number']
      var catalog_item_type_requested = urlQueryString['d_type']
      var catalog_item = undefined;
      for (var i=0; i<catalog.length; i++) {
        if (catalog[i].catalog_row_number == catalog_row_requested) {
          catalog_item = catalog[i];
          break;
        }
      }
      // display error, if item is not found
      if (catalog_item == null) {
        tableController.model = {
          ref: 'big problem!'//TODO: improve alert msg
        };
        return;
      }
      // retrieve "catalog_item_type_requested" specific item Metadata
      var item_ref_plus_dtype;
      var item_filename;
      var item_type;
      var item_classification;
      var item_res;
      var item_source;
      var item_url;
      var item_contact;
      var item_reference;
      switch (catalog_item_type_requested) {
        case '0':
          item_ref_plus_dtype = catalog_item.catalog_ref_number+.1;
          item_filename = catalog_item.bathy_filename;
          item_type = "Multibeam Bathymetry";
          item_classification = "NA";
          item_res = catalog_item.bathy_resolution;
          item_source = catalog_item.bathy_source;
          item_url = catalog_item.bathy_url;
          item_contact = catalog_item.bathymetry_contact;
          item_reference = catalog_item.bathy_reference;
          break;
        case '1':
          item_ref_plus_dtype = catalog_item.catalog_ref_number+.2;
          item_filename = catalog_item.backscatter_file_name;
          item_type = "Backscatter Imagery";
          item_classification = "NA";
          item_res = catalog_item.backscatter_resolution;
          item_source = catalog_item.backscatter_source;
          item_url = catalog_item.backscatter_url;
          item_contact = catalog_item.backscatter_contact;
          item_reference = catalog_item.backscatter_reference;
          break;
        case '4':
          item_ref_plus_dtype = catalog_item.catalog_ref_number+.4;
          item_filename = catalog_item.bathy_filename;
          item_type = "Biogenic";
          item_classification = catalog_item.classification_method;
          item_res = catalog_item.backscatter_resolution;
          item_source = catalog_item.backscatter_source;
          item_url = catalog_item.backscatter_url;
          item_contact = catalog_item.backscatter_contact;
          item_reference = catalog_item.backscatter_reference;
          break;
        case '5':
          item_ref_plus_dtype = catalog_item.catalog_ref_number+.4;
          item_filename = catalog_item.bathy_filename;
          item_type = "Effort";
          item_classification = catalog_item.classification_method;
          item_res = catalog_item.backscatter_resolution;
          item_source = catalog_item.backscatter_source;
          item_url = catalog_item.backscatter_url;
          item_contact = catalog_item.backscatter_contact;
          item_reference = catalog_item.backscatter_reference;
          break;
        default: //typically d_type == 2
          item_ref_plus_dtype = catalog_item.catalog_ref_number+.3;
          item_filename = catalog_item.habitat_file_name;
          item_type = "Habitat Map";
          item_classification = catalog_item.classification_method;
          item_res = catalog_item.habitat_resolution;
          item_source = catalog_item.habitat_source;
          item_url = catalog_item.habitat_url;
          item_contact = catalog_item.habitat_contact;
          item_reference = catalog_item.habitat_reference;
      }
      // update model
      tableController.model = {
         ref: item_ref_plus_dtype
        ,name: catalog_item.site_name
        ,filename: item_filename
        ,type: item_type
        ,format: catalog_item.habitat_format //TODO: review, is this correct for all d_types?
        ,classification: item_classification
        ,north: catalog_item.utm_extent_north_dd
        ,west: catalog_item.utm_extent_west_dd
        ,south: catalog_item.utm_extent_south_dd
        ,east: catalog_item.utm_extent_east_dd
        ,res: item_res
        ,proj: catalog_item.projection
        ,mgmt: catalog_item.management
        ,source: item_source
        ,date: catalog_item.publication_date
        ,url: item_url
        ,contact: item_contact
        ,reference: item_reference
        ,comments: catalog_item.comments
      };
    };
  }]);
