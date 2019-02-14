'use strict';
/*JavaScript, defining simple AJAX functions to populate HTML <table>s
 *
 * Copyright (C) 2016 ERT Inc.
*/
function populate_catalog_item_table (tableRowBuilderFunction) {
  // function to asynchronously retrieve default FRAM EFHRC dataset
  // as JSON text & populate an HTML model via referenced callback
  // function.
  var default_dataset = "efh.efh_catalog_fact";
  populate_fram_item_table(default_dataset, tableRowBuilderFunction);
}

function populate_fram_item_table (fram_dataset_id, tableRowBuilderFunction) {
  // function to asynchronously retrieve specified FRAM warehouse dataset
  // as JSON text & populate an HTML model via referenced callback
  // function.
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
      if (xhttp.readyState == 4 && xhttp.status == 200) {
          populateTable(xhttp.responseText, tableRowBuilderFunction);
      }
      //TODO: display error message, on failure
  };
  var api_base = "http://NwcDevFRAM.nwfsc.noaa.gov"
  var efh_uri = "/api/v1/source/"+fram_dataset_id+"/selection.json"
  xhttp.open("GET", api_base+efh_uri, true);
  xhttp.send();

  function populateTable(responseText, tableRowBuilderFunction) {
      var catalog_items = JSON.parse(responseText);
      // sort items (results from API may not be stable)
      catalog_items.sort(function(a, b) {
          return a.catalog_row_number - b.catalog_row_number;
      });
      // Add one row to table, for each item the API returned
      var table = document.getElementById("datasets")
      for (var i=0; i<catalog_items.length; i++){
        tableRowBuilderFunction(i, catalog_items, table);
      }
  }
}
