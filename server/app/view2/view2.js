'use strict';

angular.module('myApp.view2', ['ngRoute','ngMaterial','angular-loading-bar','ngSanitize','ngCookies'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/map', {
    templateUrl: 'view2/view2.html'
  }).when('/metadata/:layer', {
    templateUrl: 'view2/metadata.html'
  }).when('/metadatalist', {
    templateUrl: 'view2/metadatalist.html'
  }); //.when('/map3d', {templateUrl: 'view1/view1.html'})

}])


.controller('View2Ctrl', ['$scope','$http', '$timeout', '$mdSidenav', '$mdUtil', '$log','$q', '$mdDialog', '$mdMedia','$cookies',function($scope,$http, $timeout, $mdSidenav, $mdUtil, $log, $q,  $mdDialog, $mdMedia, $cookies) {

/*********************************************************************************************************************************************
	Fancytree spinner for reloading already client saved data
**********************************************************************************************************************************************/

var opts = {
  lines: 13 // The number of lines to draw
, length: 28 // The length of each line
, width: 14 // The line thickness
, radius: 42 // The radius of the inner circle
, scale: 1 // Scales overall size of the spinner
, corners: 1 // Corner roundness (0..1)
, color: '#000' // #rgb or #rrggbb or array of colors
, opacity: 0.25 // Opacity of the lines
, rotate: 0 // The rotation offset
, direction: 1 // 1: clockwise, -1: counterclockwise
, speed: 1 // Rounds per second
, trail: 60 // Afterglow percentage
, fps: 20 // Frames per second when using setTimeout() as a fallback for CSS
, zIndex: 2e9 // The z-index (defaults to 2000000000)
, className: 'spinner' // The CSS class to assign to the spinner
, top: '60%' // Top position relative to parent
, left: '50%' // Left position relative to parent
, shadow: false // Whether to render a shadow
, hwaccel: false // Whether to use hardware acceleration
, position: 'absolute' // Element positioning
}


var target = document.getElementById('spinner');
var spinner = new Spinner(opts).spin(target);
spinner.stop();



/*********************************************************************************************************************************************
	Meta data tool button section content
**********************************************************************************************************************************************/
var metaData = '';

var citationContent = '<h2>Citation</h2>'
+'The following language should be used to cite data retrieved from this website and using it in subsequent publication:<br><br>'
+'<i>&lt;Dataset Citation Name&gt;, NOAA Fisheries, NWFSC/FRAM, 2725 Montlake Blvd. East, Seattle, WA 98112.</i><br><br>'
+'Appropriate data set names include:<br><br>'
+'<table  class="display" cellspacing="0" width="50%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Layer Name&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Dataset Citation Name&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'
+'<tr class="metadataEven"><td>Acoustics Survey</td><td>Integrated Hake Acoustics Survey</td></tr>'
+'<tr class="metadataOdd"><td>Economics & Social Science Research</td><td>Economics & Social Science Research</td></tr>'
+'<tr class="metadataEven"><td>Habitat</td><td>Marine Habitat Program</td></tr>'
+'<tr class="metadataOdd"><td>Hook & Line Survey</td><td>Southern California Hook and Line Survey</td></tr>'
+'<tr class="metadataEven"><td>Observer Program</td><td>West Coast Groundfish Observer Program</td></tr>'
+'<tr class="metadataOdd"><td>Trawl Survey</td><td>West Coast Groundfish Bottom Trawl Survey</td></tr>'
+'        </tbody>'
+' </table>	'
+'<h2>Proper Usage</h2>'
+'The ways in which data are collected across the different FRAM programs have been carefully designed to meet certain scientific and fisheries management requirements and standards. As a result, the data cannot necessarily be generally applied to other types of analysis without understanding these collection techniques and purposes. Below we attempt to describe some of these details in hopes that the data is well understood and used properly. If you have any questions regarding these usage descriptions, please contact us via the information contained in the Contact Us button (the i button).<br><br>'
+'<h3>Observer Program</h3>'
+'The Observer program data are aggregated in order to release it in a publicly available form. We follow a rule of 3 calculation to ensure that no individual vessels can be uniquely identified in the data.'
+'<h3>Trawl Survey</h3>'
+'<h4>Catch</h4>'
+'Each survey and study data series is largely self-contained and based upon statistical designs and collection procedures that are significantly different from the other series. Consequently, these data sets are not generally amenable to combined analyses in the interest of creating longer time series. It is best to look at the following field to distinguish between these different surveys and studies:<br>'
+'<h4>Project Name (as listed in the web application, actual variable name = project when querying directly via the API)</h4>'
+'The various data sets and time ranges are:<br>'
+'<table  class="display" cellspacing="0" width="50%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Project Name&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Time Range&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Status&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>NWFSC Groundfish Slope and Shelf Combination Survey</td><td>2003-2015</td><td>Available</td></tr>'
+'<tr class="metadataOdd"><td>NWFSC Groundfish Slope Survey</td><td>1998-2002</td><td>Available</td></tr>'
+'<tr class="metadataEven"><td>NWFSC Groundfish Shelf Survey</td><td>2001</td><td>Not Yet Available</td></tr>'
+'<tr class="metadataOdd"><td>NWFSC Groundfish Triennial Shelf Survey</td><td>1977-2004 (every 3 years)</td><td>Not Yet Available</td></tr>'
+'<tr class="metadataEven"><td>NWFSC Hypoxia Study</td><td>2008-2011</td><td>Available</td></tr>'
+'<tr class="metadataOdd"><td>NWFSC Santa Barbara Basin Study</td><td>2008</td><td>Available</td></tr>'
+'<tr class="metadataEven"><td>NWFSC Video Study</td><td>2009</td><td>Available</td></tr>'
+'<tr class="metadataOdd"><td>AFSC Slope Survey	1984</td><td>1988-2001</td><td>Not Yet Available</td></tr>'

+'        </tbody>'
+' </table>	'
+'<h4>Stations</h4>'
+'The trawl survey is performed within a grid of approximately 30,146 1.5nmi x 2.0nmi stations along the west coast (check the Trawl Survey > Station Grids layer to see a visual depiction of these). Most of these grid cells fall outside the defined depth range of the current slope/shelf combined survey and many have been removed from sampling due to protected area and other permitting restrictions. Currently we are left with 11,508 grid cells as candidate survey target stations. Therefore a grid that may have yielded catch from a given species in an earlier year will have zero probability of catch in later years if the grid has been removed from the sampling plan altogether. In such cases, data from tows made in grid cells that were subsequently removed from the survey design should not be included in data sets intended for trends analysis in order to prevent introducing bias into the results. One can quickly determine if and when a station was removed by examining the station removal date:'
+'<h4>Date Station Invalid (as listed in the web application, actual variable name = target_station_design_dim$date_stn_invalid_for_trawl_whid when querying directly via the API)</h4>';



var apiContent='<h2>Application Programming Interface (API)</h2>'
+'<h3>Getting Started - Your First RESTful API Query</h3>'
+'The following URL shows a sample query for Petrale sole (scientific name = Eopsetta jordani), against the trawl survey catch data, from 2010 until 2012:<br><br>'
+'<i>json output</i><br>'
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012&variables=date_yyyymmdd,field_identified_taxonomy_dim$scientific_name" target="_blank">https:\/\/www.nwfsc.noaa.gov\/data\/api\/v1\/source\/trawl.catch_fact\/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012<br>&variables=date_yyyymmdd,field_identified_taxonomy_dim$scientific_name</a><br><br>'
+'Click on it and you should get back a stream of json-formatted data in your web browser that shows the date and scientific name that looks like the following:<br><br>'
+'<table  class="display" cellspacing="0" width="60%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Sample json output&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>[{"date_yyyymmdd": "20121009", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_yyyymmdd": "20100822", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_yyyymmdd": "20100822", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_yyyymmdd": "20100824", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"}, </td></tr>'


+'        </tbody>'
+' </table>	<br><br>'
+'If you\'d prefer a csv download of the data, change selection.json to selection.csv as follows:<br><br>'
+'<i>csv output</i><br>'
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.csv?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012&variables=date_yyyymmdd,field_identified_taxonomy_dim$scientific_name" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.csv?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012><br>&variables=date_yyyymmdd,field_identified_taxonomy_dim$scientific_name</a><br><br>'
+'<h3>Dissecting the URL</h3>'
+'Now let\'s dissect the components of the URL to understand what is happening:<br>'
+'<img src="images/QueryURL.png" WIDTH="770" HEIGHT="507" BORDER=0 ALT="Query URL"/><br><br>'
+'<table  class="display" cellspacing="0" width="50%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Component&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Description&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Example&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>Base URL</td><td>Base URL for the API</td><td>https://www.nwfsc.noaa.gov/data/api/v1/source</td></tr>'
+'<tr class="metadataOdd"><td>Layer</td><td>Name of the layer you\'re querying. A listing of all layers can be obtained at the following url: <a href="https://www.nwfsc.noaa.gov/data/api/v1/source/" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/</a>. Note that the layer names are called id at this URL.</td><td>trawl.catch_fact</td></tr>'
+'<tr class="metadataEven"><td>Content</td><td>The type of content you want to receive. Possibilities include selection.json, selection.csv, and variables (to get a listing of variables for the layer)</td><td>selection.json</td></tr>'
+'<tr class="metadataOdd"><td>Query Filters</td><td>This will start with filters= and then is appended with a listing of key=value pairs separated by commas</td><td>filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012</td></tr>'
+'<tr class="metadataEven"><td>Requested Variables</td><td>List of variables, comma separated, that you want to return, leave blank to return all variables (but this will incur a performance hit due to the large number of variables)</td><td>variables=date_yyyymmdd,field_identified_taxonomy_dim$scientific_name</td></tr>'
+'<tr class="metadataOdd"><td>Complete URL</td><td>The full URL</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012&variables=date_yyyymmdd,field_identified_taxonomy_dim$scientific_name" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012<br>&variables=date_yyyymmdd,field_identified_taxonomy_dim$scientific_name</a></td></tr>'

+'        </tbody>'
+' </table>	<br><br>'
+'It is important to note that the content type is followed by an ? symbol and between the filters and variables is an & symbol. Now it is simply a matter of identifying which layer you want to query, what are your query filters, and which variables you want to return from that query.<br><br>'
+'<h3>Key Layers to Query</h3>'
+'The key layers that you\'ll most likely want to query include:<br><br>'
+'<table  class="display" cellspacing="0" width="50%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Content&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Layer ID&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Layer Variables URL&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>Trawl Survey Catch</td><td>trawl.catch_fact&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/variables</a></td></tr>'
+'<tr class="metadataOdd"><td>Trawl Survey Specimens</td><td>trawl.individual_fact&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.individual_fact/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.individual_fact/variables</a></td></tr>'
+'<tr class="metadataEven"><td>Trawl Survey Haul Characteristics (includes environmental data)</td><td>trawl.operation_haul_fact&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.operation_haul_fact/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.operation_haul_fact/variables</a></td></tr>'
+'<tr class="metadataOdd"><td>Hook & Line Survey Catch</td><td>hooknline.catch_hooknline_view&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/hooknline.catch_hooknline_view/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/hooknline.catch_hooknline_view/variables</a></td></tr>'
+'<tr class="metadataEven"><td>Hook & Line Survey Specimens</td><td>	hooknline.individual_hooknline_view&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/hooknline.individual_hooknline_view/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/hooknline.individual_hooknline_view/variables</a></td></tr>'
+'<tr class="metadataOdd"><td>Hook & Line Survey Site Characteristics (includes environmental data)</td><td>warehouse.operation_hook_fact&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/warehouse.operation_hook_fact/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/warehouse.operation_hook_fact/variables</a></td></tr>'
+'<tr class="metadataEven"><td>Observer Aggregated Catch</td><td>observer.catch_observer_view&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/observer.catch_observer_view/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/observer.catch_observer_view/variables</a></td></tr>'

+'        </tbody>'
+' </table>	'
+'<h2>Detailed Reference Documentation</h2>'
+'<h3>Overview</h3>'
+'The FRAM Data Warehouse provides a rich RESTful API that can be used by external software programs to retrieve data. Designed as a data warehouse, it contains two types of tables:'
+'<ul><li><b>Dimension Tables</b> - These contain the parameters by which users typically want to query the data. For instance, date and time values are dimension tables.</li>'
+'<li><b>Fact Tables</b> - These contain the measured values of the information that FRAM has collected. For instance, the trawl survey catch data is a fact table.</li></ul>'
+'<h3>URL Endpoints</h3>'
+'There are three primary URL endpoints in the API. These are RESTful URLs and, by appending parameters to these URLs, enable users to directly query against the data warehouse. The endpoints are:<br><br>'
+'<h4><i>Source</i></h4>'
+'The source endpoint contains listing of all of the dimension and fact tables, some basic metadata about them, and can be found at the following url:<br>'
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/</a><br><br>'
+'Critically important for each layer identified in the source URL is the id element. This id element is what is subsequently used to query for layer variables and actual layer data. A sample layer entry looks like the following:<br>'
+'<table  class="display" cellspacing="0" width="60%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Source sample layer entry&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>{'
+'	"description": "latitude_dim",<br>'
+'	"project": "warehouse",<br>'
+'	"name": "latitude_dim",<br>'
+'        "contact": "N/A",<br>'
+'	"years": null,<br>'
+'	"updated": "2016-01-22T17:22:45.199689Z",<br>'
+'	"rows": -1,<br>'
+'        "id": "warehouse.latitude_dim"<br>'
+'},</td></tr>'


+'        </tbody>'
+' </table>	'
+'So in this instance, the id is warehouse.latitude_dim. This means that we\'re looking at a dimension table (notice the _dim suffix) that contains latitude information. Alternatively, an id can end in _fact or _view that represent fact tables and views respectively (Our fact views are actually database views built on top of other fact tables, thus the _view suffix in certain cases).'
+'<h4><i>Layer Variables</i></h4>'
+'The various layers variables endpoints provide a listing of all of the available variables for a given layer. The URL includes the name of the layer as provided in the source URL above. So, for instance, one could get all of the available variables for the trawl.catch_fact layer (which contains the Trawl Survey Catch data) at the following URL:<br>'
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/variables" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/variables</a><br><br>'
+'Note the "trawl.catch_fact" parameter in the URL, indicating the layer of interest.<br>'
+'<h4><i>Selection</i></h4>'
+'The selection endpoint allows a user to actually retrieve the data. A basic selection URL for the trawl survey catch layer looks like the following:<br>'
+'<table  class="display" cellspacing="0" width="50%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Output Format&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Endpoint&nbsp;&nbsp;&nbsp;</th>'
+'                <th>Example&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>json</td><td>selection.json&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json</a></td></tr>'
+'<tr class="metadataOdd"><td>csv</td><td>selection.csv&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.csv" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.csv</a></td></tr>'

+'        </tbody>'
+' </table>	'
+'<h4>Query Filters</h4>'
+'One can add comma-separated query filters to the ending of the selection endpoint to query for a filtered dataset as follows:<br>'
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Sebastes%20aurora,date_dim$year=2014" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?<br>filters=field_identified_taxonomy_dim$scientific_name=Sebastes%20aurora,date_dim$year=2014</a><br><br>'
+'The following filter operations are supported:<br>'
+'<table  class="display" cellspacing="0" width="60%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Supported Filtering Operations&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>{variable} = {value}<br>'
+'{variable} > {value}<br>'
+'{variable} < {value}<br>'
+'{variable} >= {value}<br>'
+'{variable} <= {value}<br>'
+'{variable} != {value}<br>'
+'{variable} ~= {value}<br>'
+'{variable} |= {value}</td></tr>'


+'        </tbody>'
+' </table><br>	'
+'\'~=\' provides Regular Expression matching e.g.:<br>'
+'filters=MyFieldName~=321 - matches any occurence of \'321\' in the field\'s text<br>'
+'filters=MyFieldName~=^321$ matches any row with exactly value \'321\' in the field<br>'
+'filters=MyFieldName~=^(321)|(987)$ matches any row with exactly value \'321\' in the field or value \'987\'<br><br>'
+'\'|=\' provides OR matching with robust type support, via an urlencoded-comma (%2C) separated list of quoted string values enclosed in square brackets e.g.:<br>'
+'_filters=MyFieldName|=["321"] - matches any record with exactly a value of 321 (converted from a string, into the type of the field).<br>'
+'_filters=MyFieldName|=["321"%2C"987"] - matches any records with an exact value of either 321 or 987.<br>'
+'<h4>Subsetted Variables</h4>'
+'One can provide a list of comma-separated list of variable names for subsetting what variables are returned from the query as follows:'
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?variables=field_identified_taxonomy_dim$scientific_name,date_dim$year" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?<br>variables=field_identified_taxonomy_dim$scientific_name,date_dim$year</a>';
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/</a><br><br>'


var contactUsContent='Please contact us with feedback, questions, and any requests that you might have regarding the FRAM Data Warehouse at the following email:<br><br>'
+'<a href="mailto:nmfs.nwfsc.fram.data.team@noaa.gov" >nmfs.nwfsc.fram.data.team@noaa.gov</a><br><br>'
+'You may also contact the FRAM Data Team lead directly at:<br><br>'
+'Todd Hay<br>'
+'NWFSC/FRAM<br>'
+'<a href="mailto:todd.hay@noaa.gov" >todd.hay@noaa.gov</a><br>'
+'206.302.2449';



var aboutUsContent='<h2>About</h2>'
+'The FRAM Data Warehouse aims to provide a single location where users can access and download all data collected by the <a href="http://www.nwfsc.noaa.gov/" target="_blank">NOAA Northwest Fisheries Science Center (NWFSC)</a> <a href="http://www.nwfsc.noaa.gov/research/divisions/fram/index.cfm" target="_blank">Fishery Resource Analysis & Monitoring (FRAM)</a> division. This includes data from the following FRAM programs/surveys:<br>'
+'<ul><li>Acoustics Survey - Integrated Hake Acoustics Survey</li>'
+'<li>Economics & Social Science Research (ESSR)</li>'
+'<li>Hook & Line Survey - Southern California Hook & Line Survey</li>'
+'<li>Marine Habitat Program</li>'
+'<li>Observer Program - West Coast Groundfish Observer Program (WCGOP)</li>'
+'<li>Trawl Survey - West Coast Groundfish Bottom Trawl Survey (WCGBTS)</li></ul>'
+'<h2>Customer Survey</h2>'
+'We welcome your feedback. Please provide this via the following customer survey:'
+'<p><a href="https://goo.gl/forms/gAYKsUANPBboWtxP2" target="_blank">Take the Survey</a></p>'
+'<p>Paperwork Reduction Act Information<br/>(OMB Control Number 0648-0342)<br/>Expires 06/30/2021</p>'
+'<h2>Privacy Policy</h2>'
+'We take your privacy very seriously and we follow the standard NOAA privacy policy that is outlined here: <a href="http://www.noaa.gov/protecting-your-privacy" target="_blank">http://www.noaa.gov/protecting-your-privacy</a>'
+'<h2>External Link Endorsement</h2>'
+'The appearance of external links on this Web site does not constitute endorsement by the Department of Commerce/National Oceanic and Atmospheric Administration of external Web sites or the information, products or services contained therein. For other than authorized activities, the Department of Commerce/NOAA does not exercise any editorial control over the information you may find at these locations. These links are provided consistent with the stated purpose of this Department of Commerce/NOAA Web site.';


/*********************************************************************************************************************************************
	Meta data tool button events/binds
**********************************************************************************************************************************************/
//	$( "#about" ).bind( "click", function( ev ) {
//			$mdDialog.show(
//			  $mdDialog.alert()
//				.parent(angular.element(document.querySelector('#popupContainer')))
//				.clickOutsideToClose(true)
//			//	.title('About / Project Updates')
//				.htmlContent(aboutUsContent)
//				.ariaLabel('About / Project Updates')
//				.ok('Close')
//				.targetEvent(ev)
//			);
//
//	});
//
//	$("#about").mousedown(function() {
//
//		$(this).attr("src","images/info click.png");
//	});
//
//	$("#about").hover(function() {
//		$(this).attr("src","images/info hover.png");
//		$(this).css("cursor", "pointer");
//	//	$(this).css(
//    //        "box-shadow", "0px 0px 2px 1px #AAEEFF"
//    //    );
//			}, function() {
//		$(this).attr("src","images/info_white.png");
//		 $(this).css( "box-shadow", "none" );
//	});
//
//
//	$( "#contactUs" ).bind( "click", function( ev ) {
//			$mdDialog.show(
//			  $mdDialog.alert()
//				.parent(angular.element(document.querySelector('#popupContainer')))
//				.clickOutsideToClose(true)
//				.title('Contact Us')
//				.htmlContent(contactUsContent)
//				.ariaLabel('Contact Us')
//				.ok('Close')
//				.targetEvent(ev)
//			);
//
//	});
//
//	$("#contactUs").mousedown(function() {
//
//		$(this).attr("src","images/email click.png");
//	});
//
//	$("#contactUs").hover(function() {
//		$(this).attr("src","images/email hover.png");
//		$(this).css("cursor", "pointer");
//	//	$(this).css(
//    //        "box-shadow", "0px 0px 2px 1px #AAEEFF"
//    //    );
//			}, function() {
//		$(this).attr("src","images/email_white.png");
//		 $(this).css( "box-shadow", "none" );
//	});
//
//	$( "#api" ).bind( "click", function( ev ) {
//			$mdDialog.show(
//			  $mdDialog.alert()
//				.parent(angular.element(document.querySelector('#popupContainer')))
//				.clickOutsideToClose(true)
//		//		.title('API')
//				.htmlContent(apiContent)
//				.ariaLabel('API')
//				.ok('Close')
//				.targetEvent(ev)
//			);
//
//	});
//	$("#api").mousedown(function() {
//
//		$(this).attr("src","images/api click.png");
//	});
//
//	$("#api").hover(function() {
//		$(this).attr("src","images/api hover.png");
//		$(this).css("cursor", "pointer");
//	//	$(this).css(
//    //        "box-shadow", "0px 0px 2px 1px #AAEEFF"
//    //    );
//			}, function() {
//		$(this).attr("src","images/api_white.png");
//		 $(this).css( "box-shadow", "none" );
//	});
//
//	$( "#citation" ).bind( "click", function( ev ) {
//			$mdDialog.show(
//			  $mdDialog.alert()
//				.parent(angular.element(document.querySelector('#popupContainer')))
//				.clickOutsideToClose(true)
//			//	.title('Citation')
//				.htmlContent(citationContent)
//				.ariaLabel('Citation')
//				.ok('Close')
//				.targetEvent(ev)
//			);
//
//	});
//
//
//	$("#citation").mousedown(function() {
//
//		$(this).attr("src","images/chat click.png");
//
//	});
//
//	$("#citation").hover(function() {
//		$(this).attr("src","images/chat hover.png");
//		$(this).css("cursor", "pointer");
//	//	$(this).css(
//    //        "box-shadow", "0px 0px 2px 1px #AAEEFF"
//    //    );
//			}, function() {
//		$(this).attr("src","images/chat_white.png");
//		 $(this).css("box-shadow", "none");
//	});
//
//	$( "#login" ).bind( "click", function( ev ) {
//			$scope.showAdd(ev);
//
//	});
//
//
//
//	$("#login").mousedown(function() {
//
//		$(this).attr("src","images/lock click.png");
//	});
//
//	$("#login").hover(function() {
//		$(this).attr("src","images/lock hover.png");
//		$(this).css("cursor", "pointer");
//
//			}, function() {
//		$(this).attr("src","images/lock white.png");
//		 $(this).css( "box-shadow", "none" );
//	});


//Metadata modal dialog window retrieval
$scope.showAlert = function(ev) {

	if (metaData != '')
		displayMetadata(metaData,ev);
	else
	{
		$http.get(api_base_uri+'/api/v1/source').success(function(data){
			var lastDateUpdated;
			for(var i=0; i<data.sources.length; i++)
			{
				if (data.sources[i].name.includes("fact") || data.sources[i].name.includes("view"))
				{
                    lastDateUpdated = new Date(data.sources[i].updated);
                    lastDateUpdated = (lastDateUpdated.getMonth() + 1) +'/'+ lastDateUpdated.getDate() +'/'+ lastDateUpdated.getFullYear()
                        +' '+lastDateUpdated.getHours()+':'+lastDateUpdated.getMinutes() +':'+lastDateUpdated.getSeconds();

                    if(i%2==0)
                        metaData +='<tr class="metadataEven"><td>'+data.sources[i].project+'</td>';
                    else
                        metaData +='<tr class="metadataOdd"><td>'+data.sources[i].project+'</td>';

                    metaData +='<td>'+data.sources[i].name+'</td>';
//                    metaData +='<td><a href="api/v1/source/'+data.sources[i].project+'.'+data.sources[i].name+'/selection.csv" target="_blank">Data</a></td>';
//                    metaData +='<td><a href="metadata/'+data.sources[i].project+'.'+data.sources[i].name+'" target="_blank">Metadata</a></td>';
                    metaData +='<td>'+data.sources[i].description+'</td>';
                    metaData +='<td>'+data.sources[i].years+'</td>';
                    metaData +='<td>'+data.sources[i].contact.replace("<","").replace(">","")+'</td>';
                    metaData +='<td>'+lastDateUpdated+'</td></tr>';
				}

			}


			displayMetadata(metaData,ev);


		});
	}


  };



   /**
     * Display Metadata dialog window
     */
    function displayMetadata(metaData,ev) {
			$mdDialog.show(
			  $mdDialog.alert()
				.parent(angular.element(document.querySelector('#popupContainer')))
				.clickOutsideToClose(true)
				.title('Metadata')
				.htmlContent('<table id="metadata_table" class="display" cellspacing="0" width="100%">'+
		'        <thead align="left">'+
		'            <tr class="metadataHeader">'+
		'                <th>Project&nbsp;&nbsp;&nbsp;</th>'+
		'                <th>Layer&nbsp;&nbsp;&nbsp;</th>'+
//		'                <th>Data&nbsp;</th>'+
//		'                <th>Metadata&nbsp;</th>'+
		'                <th>Description&nbsp;&nbsp;&nbsp;</th>'+
		'                <th>Years of Data</th>'+
			'                <th>Point of Contact</th>'+
		'                <th>Updated&nbsp;&nbsp;&nbsp;</th>'+



		'            </tr>'+
		'        </thead>'+
		'        <tbody>'+
					metaData +
			'        </tbody>'+
		   ' </table>	')
				.ariaLabel('Metadata')
				.ok('Close')
				.targetEvent(ev)
			);

    }



/*********************************************************************************************************************************************
	LeafletJS initialization
**********************************************************************************************************************************************/

	var imagery =  L.esri.basemapLayer('Imagery'),
		shadedrelief =  L.esri.basemapLayer('ShadedRelief'),
		oceans =  L.esri.basemapLayer('Oceans'),
		topographic =  L.esri.basemapLayer('Topographic'),
		nationalGeographic =  L.esri.basemapLayer('NationalGeographic'),
		rnc_image = L.tileLayer('https://tileservice.charts.noaa.gov/tiles/50000_1/{z}/{x}/{y}.png');


   var map = L.map('map', { zoomControl: false , layers: oceans}).setView([39.351, -116.48], 5);

	var baseMaps = {
			  "Imagery" : imagery,
			  "Shaded Relief" : shadedrelief,
			  "Oceans" : oceans,
			  "Topographic" : topographic,
			  "National Geographic": nationalGeographic,
			  "NOAA Nautical Charts": rnc_image
	};

	L.control.layers(baseMaps,null,{ position: 'topleft' }).addTo(map);
	L.control.scale({ position: 'bottomleft' }).addTo(map);

	//Handle latitude/longitude display at the bottom right of the map
	map.on('mousemove', function(e) {
	   $("#lat-long").html('Latitude: ' + e.latlng.lat.toFixed(6)+ '<br> Longitude: ' + e.latlng.lng.toFixed(6) );
	});

	map.createPane('custom');

    $("#legend").hide();
    $("#legend-rectangle").hide();

/*********************************************************************************************************************************************
	Add easyButtons
**********************************************************************************************************************************************/

    L.easyButton({
      states: [{
        icon: 'fa-lock fa-2x',
        title: 'Login',
        onClick: function(control,ev) {
          $scope.showAdd(ev);
        }
      }]
    }).addTo( map );

    L.easyButton({
      states: [{
        icon: 'fa-quote-right fa-2x',
        title: 'Citation and Proper Usage',
        onClick: function(control,ev) {
            $mdDialog.show(
			  $mdDialog.alert()
				.parent(angular.element(document.querySelector('#popupContainer')))
				.clickOutsideToClose(true)
				.htmlContent(citationContent)
				.ariaLabel('Citation')
				.ok('Close')
				.targetEvent(ev)
			);
        }
      }]
    }).addTo( map );

    L.easyButton({
      states: [{
        icon: 'fa-database fa-2x',
        title: 'Application Programming Interfaces (API)',
        onClick: function(control,ev) {
			$mdDialog.show(
			  $mdDialog.alert()
				.parent(angular.element(document.querySelector('#popupContainer')))
				.clickOutsideToClose(true)
				.htmlContent(apiContent)
				.ariaLabel('API')
				.ok('Close')
				.targetEvent(ev)
			);
        }
      }]
    }).addTo( map );

    L.easyButton({
      states: [{
        icon: 'fa-tags fa-2x',
        title: 'Metadata',
        onClick: function(control,ev) {
            window.open("/data/metadatalist");
        }
      }]
    }).addTo( map );

    L.easyButton({
      states: [{
        icon: 'fa-envelope-open fa-2x',
        title: 'Contact Us',
        onClick: function(control,ev) {
			$mdDialog.show(
			  $mdDialog.alert()
				.parent(angular.element(document.querySelector('#popupContainer')))
				.clickOutsideToClose(true)
				.title('Contact Us')
				.htmlContent(contactUsContent)
				.ariaLabel('Contact Us')
				.ok('Close')
				.targetEvent(ev)
			);
        }
      }]
    }).addTo( map );

    L.easyButton({
      states: [{
        icon: 'fa-info fa-2x',
        title: 'About FRAM Data Warehouse',
        onClick: function(control,ev) {
			$mdDialog.show(
			  $mdDialog.alert()
				.parent(angular.element(document.querySelector('#popupContainer')))
				.clickOutsideToClose(true)
			//	.title('About / Project Updates')
				.htmlContent(aboutUsContent)
				.ariaLabel('About / Project Updates')
				.ok('Close')
				.targetEvent(ev)
			);
        }
      }]
    }).addTo( map );

    var measureControl = new L.Control.Measure({position: 'topleft', captureZIndex: 10000 });
    measureControl.addTo(map);

	new L.Control.Zoom({ position: 'topleft' }).addTo(map);
/*********************************************************************************************************************************************
	Main app layout initialization
**********************************************************************************************************************************************/

	var mainLayout = $('body').layout({


			center__paneSelector: "#paneCenter",
			west__paneSelector: "#paneWest",
			east__paneSelector: "#paneEast",
			south__paneSelector: "#paneSouth",
			west__minSize:			350,
			east__initClosed: true,
			south__initClosed: true,
			south__minSize: 100

	});

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
		api_base_uri = 'https://nwcdevfram.nwfsc.noaa.gov';
	else if(api_base_uri.indexOf("devwww11")>=0)
		api_base_uri = 'https://devwww11.nwfsc.noaa.gov/data';
	else
		api_base_uri = 'https://www.nwfsc.noaa.gov/data';

/*********************************************************************************************************************************************
	variable initialization
**********************************************************************************************************************************************/
	$scope.programBtnChecked = true;
	$scope.showTimeplayer = true;

	$scope.disableSpeciesFilter = true;
	var self = this;
	var j_cycleStartDate = '1/1/1900';
	var j_cycleEndDate = '1/1/3000';

    // external user, new account creation base path
    var register_base_uri = 'https://nwcdevfram.nwfsc.noaa.gov:8543/auth';

	var randomColor = new Dict();
	var today = new Date();
    self.readonly = false;
    self.selectedItem = null;
    self.searchText = null;
    self.querySearch = querySearch;
    self.selectedSpecies = [];

	//Time filter default start/end date
    self.cycleStartDate = new Date(today.getFullYear()-3,today.getMonth(),today.getDate());
    self.cycleEndDate = new Date();

	//species selected
	$scope.selected = [];

	//layers selected
    self.checkedLayers = [];

	var haulCharDataSourceStartDt;
	var haulCharDataSourceEndDt;
	self.mapHeight ;


	//the following 2 hashmaps keep track of the
	//indices of the map point primitives to be used
	//for show/hide
	var layerToPrimitiveDict = new Dict();

	//cancelers are used to cancel an API call when users decide to
	//uncheck a layer after an API call is underway
	var hookLineSpecimenCanceler = $q.defer();
	var hookLineCatchCanceler = $q.defer();
	var trawlCatchCanceler = $q.defer();
	var trawlHaulCharsCanceler = $q.defer();
	var trawlSpecimensCanceler = $q.defer();
	var timeplayerDefer = $q.defer();
	var observerCatchCanceler = $q.defer();

	var timefilterData = {};

	//Predefined allowable Leaflet marker colors

	var leafletMarkerColorArray = ['orange','green','cyan', 'yellow',  'purple','red', 'orange-dark', 'blue','blue-dark',
		 'violet', 'pink', 'green-dark', 'green-light', 'white','black'];
	var leafletMarkerColorCounter = 0;

	//showProgram, showDataType is used to toggle between fancy tree groups
	var currentFancyTree = '#layers';
	$scope.showProgram = function() {
		$scope.programBtnChecked = true;
		currentFancyTree = '#layers';
	};
//	$scope.showDataType = function() {
//		$scope.programBtnChecked = false;
//		currentFancyTree = '#layers-content';
//	};

	$scope.showPlayer = function() {
		$scope.showTimeplayer = true;
	};
	$scope.showDates = function() {
		$scope.showTimeplayer = false;
	};


	//ArcGIS layer array
	var allLayers = new Array();
	var allLayerLegends = new Array();

    //used for finding the node to zoom in and out to
    var foundNode = null;

/*********************************************************************************************************************************************
	FancyTree initialization / layer ordering
**********************************************************************************************************************************************/

	$("#layers").fancytree({
	  source: [
		  		{title: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.key, folder: true, children: [
		  {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.title+'" href="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.url+'" >'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.title+'</a>', key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.key, data:{/*layer:acousticsNASC2012Layer , */url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.mapServices}, icon: false},
		  {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.title+'" href="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.url+'" >'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.title+'</a>', key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.key, data:{/*layer:acousticsNASC2013Layer , */url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.mapServices}, icon: false},
		  {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.title+'" href="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.url+'" >'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.title+'</a>', key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.key, data:{/*layer:acousticsNASC2015Layer , */url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.mapServices}, icon: false},
		  {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.title+'" href="'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.url+'" >'+FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.title+'</a>', key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.key, data:{/*layer:acousticsSonarDataLayer,*/url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.mapServices}, icon: false}
		]},

		{title: FANCYTREE_ITEMS.EFH.title, key: FANCYTREE_ITEMS.EFH.key, folder: true,  children: [
			  {title: FANCYTREE_ITEMS.EFH.AMENDMENT_19.title, key: FANCYTREE_ITEMS.EFH.AMENDMENT_19.key, folder: true, icon: true, children: [
			       {title: FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.title, key: FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.key, folder: true,  children: [
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_CONSERVATION_AREAS.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_CONSERVATION_AREAS.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_CONSERVATION_AREAS.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_CONSERVATION_AREAS.key, data:{/*layer:efhAmendment19EfhConservationAreaMapLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_CONSERVATION_AREAS.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_CONSERVATION_AREAS.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_700_BOTTOM_TRAWL.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_700_BOTTOM_TRAWL.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_700_BOTTOM_TRAWL.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_700_BOTTOM_TRAWL.key, data:{/*layer:efhAmendment19Efh700BottomMapLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_700_BOTTOM_TRAWL.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_700_BOTTOM_TRAWL.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_DESIGNATED_AREAS.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_DESIGNATED_AREAS.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_DESIGNATED_AREAS.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_DESIGNATED_AREAS.key, data:{/*layer:efhAmendment19EfhDesignatedMapLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_DESIGNATED_AREAS.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_19.EFH.EFH_DESIGNATED_AREAS.mapServices}, icon: false}
				    ]}
				]},
			  {title: FANCYTREE_ITEMS.EFH.AMENDMENT_28.title, key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.key, folder: true, icon: true, children: [
			       {title: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.title, key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.key, folder: true,  children: [
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1.key, data:{/*layer:efhAmendment28EfhAlt1Layer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1A.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1A.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1A.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1A.key, data:{/*layer:efhAmendment28EfhAlt1aLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1A.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1A.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1B.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1B.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1B.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1B.key, data:{/*layer:efhAmendment28EfhAlt1bLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1B.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1B.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1C.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1C.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1C.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1C.key, data:{/*layer:efhAmendment28EfhAlt1cLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1C.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1C.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1D.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1D.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1D.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1D.key, data:{/*layer:efhAmendment28EfhAlt1dLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1D.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1D.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1E.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1E.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1E.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1E.key, data:{/*layer:efhAmendment28EfhAlt1eLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1E.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1E.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1F.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1F.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1F.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1F.key, data:{/*layer:efhAmendment28EfhAlt1fLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1F.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1F.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1G.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1G.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1G.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1G.key, data:{/*layer:efhAmendment28EfhAlt1gLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1G.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1G.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1H.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1H.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1H.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1H.key, data:{/*layer:efhAmendment28EfhAlt1gLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1H.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_1H.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_3.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_3.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_3.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_3.key, data:{/*layer:efhAmendment28EfhAlt3Layer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_3.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.EFH.ALT_3.mapServices}, icon: false}
				    ]},
				   {title: FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.title, key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.key, folder: true, icon: true, children: [
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2.key, data:{/*layer:efhAmendment28RcaAlt2MapLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2A.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2A.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2A.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2A.key, data:{/*layer:efhAmendment28RcaAlt2aMapLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2A.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2A.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2B.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2B.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2B.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2B.key, data:{/*layer:efhAmendment28RcaAlt2bMapLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2B.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2B.mapServices}, icon: false},
					 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2C.title+'" href="'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2C.url+'" >'+FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2C.title+'</a>', key: FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2C.key, data:{/*layer:efhAmendment28RcaAlt2cMapLayer  , */url:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2C.url, mapServices:FANCYTREE_ITEMS.EFH.AMENDMENT_28.RCA.ALT_2C.mapServices}, icon: false}
				    ]}
				]},
                  {title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.key, folder: true,  children: [
                        {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.title+'" href="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.url+'" >'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.title+'</a>', key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.key, data:{/*layer:spatialReferencesHabitat36140MapLayer  , */url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.mapServices}, icon: false}/*,
                        {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.title+'" href="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.url+'" >'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.title+'</a>', key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.key, data:{layer:spatialReferencesHabitat361MapLayer  , url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.mapServices}, icon: false},
                        {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.title+'" href="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.url+'" >'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.title+'</a>', key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.key, data:{layer:spatialReferencesHabitat40MapLayer  , url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.mapServices}, icon: false}*/
                    ]},
                  {title: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.title, key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.key, folder: true, icon: true, children: [
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2011_2015.title+'" href="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2011_2015.url+'" >'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2011_2015.key, data:{/*layer:efhFishingEffortBottom2011_2015MapLayer  , */url:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2011_2015.url, mapServices:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2011_2015.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2006_2010.title+'" href="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2006_2010.url+'" >'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2006_2010.title+'</a>', key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2006_2010.key, data:{/*layer:efhFishingEffortBottom2006_2010MapLayer  , */url:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2006_2010.url, mapServices:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2006_2010.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2002_2006.title+'" href="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2002_2006.url+'" >'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2002_2006.title+'</a>', key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2002_2006.key, data:{/*layer:efhFishingEffortBottom2002_2006MapLayer  , */url:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2002_2006.url, mapServices:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.BOTTOM_TRAWL_2002_2006.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2006_2010.title+'" href="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2006_2010.url+'" >'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2006_2010.title+'</a>', key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2006_2010.key, data:{/*layer:efhFishingEffortFixedGear2006_2010MapLayer  , */url:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2006_2010.url, mapServices:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2006_2010.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2002_2006.title+'" href="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2002_2006.url+'" >'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2002_2006.title+'</a>', key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2002_2006.key, data:{/*layer:efhFishingEffortFixedGear2002_2006MapLayer  , */url:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2002_2006.url, mapServices:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.FIXED_GEAR_2002_2006.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2006_2010.title+'" href="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2006_2010.url+'" >'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2006_2010.title+'</a>', key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2006_2010.key, data:{/*layer:efhFishingEffortMidTrawl2006_2010MapLayer  , */url:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2006_2010.url, mapServices:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2006_2010.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2002_2006.title+'" href="'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2002_2006.url+'" >'+FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2002_2006.title+'</a>', key: FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2002_2006.key, data:{/*layer:efhFishingEffortMidTrawl2002_2006MapLayer  , */url:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2002_2006.url, mapServices:FANCYTREE_ITEMS.EFH.FISHING_EFFORT.MID_TRAWL_2002_2006.mapServices}, icon: false}
                    ]},
                  {title: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.title, key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.key, folder: true, icon: true, children: [
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_OBS.title+'" href="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_OBS.url+'" >'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_OBS.title+'</a>', key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_OBS.key, data:{/*layer:efhSpeciesDistributionCoralSpongeObsMapLayer  , */url:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_OBS.url, mapServices:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_OBS.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_PRESENCE.title+'" href="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_PRESENCE.url+'" >'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_PRESENCE.title+'</a>', key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_PRESENCE.key, data:{/*layer:efhSpeciesDistributionCoralSpongePresMapLayer  , */url:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_PRESENCE.url, mapServices:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_SPONGE_PRESENCE.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_PRESENCE.title+'" href="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_PRESENCE.url+'" >'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_PRESENCE.title+'</a>', key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_PRESENCE.key, data:{/*layer:spongePresencehMapLayer  , */url:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_PRESENCE.url, mapServices:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_PRESENCE.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_PRES.title+'" href="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_PRES.url+'" >'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_PRES.title+'</a>', key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_PRES.key, data:{/*layer:seaPenWhipPresMapLayer  , */url:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_PRES.url, mapServices:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_PRES.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_BYCATCH.title+'" href="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_BYCATCH.url+'" >'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_BYCATCH.title+'</a>', key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_BYCATCH.key, data:{/*layer:efhGeneralCoralBycatchMapLayer  , */url:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_BYCATCH.url, mapServices:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.CORAL_BYCATCH.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_BYCATCH.title+'" href="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_BYCATCH.url+'" >'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_BYCATCH.title+'</a>', key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_BYCATCH.key, data:{/*layer:spongeBycatchMapLayer  , */url:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_BYCATCH.url, mapServices:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SPONGE_BYCATCH.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_BYCATCH.title+'" href="'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_BYCATCH.url+'" >'+FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_BYCATCH.title+'</a>', key: FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_BYCATCH.key, data:{/*layer:seaPenWhipBycatchMapLayer  , */url:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_BYCATCH.url, mapServices:FANCYTREE_ITEMS.EFH.SPECIES_DISTRIBUTION.SEA_PEN_WHIP_BYCATCH.mapServices}, icon: false}
                    ]},
                  {title: FANCYTREE_ITEMS.EFH.GENERAL.title, key: FANCYTREE_ITEMS.EFH.GENERAL.key, folder: true, icon: true, children: [
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.key, data:{/*layer:efhGeneralGroundfishTrawlPoly20152016MapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.mapServices}, icon: false},
					     {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.key, data:{/*layer:efhGeneralGroundfishTrawlLines20152016MapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.TRIBAL_USUAL_ACCUSTOMED_AREAS.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.TRIBAL_USUAL_ACCUSTOMED_AREAS.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.TRIBAL_USUAL_ACCUSTOMED_AREAS.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.TRIBAL_USUAL_ACCUSTOMED_AREAS.key, data:{/*layer:tribalUsualAccustomedAreasMapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.TRIBAL_USUAL_ACCUSTOMED_AREAS.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.TRIBAL_USUAL_ACCUSTOMED_AREAS.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.PFMC_LANDMARKS.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.PFMC_LANDMARKS.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.PFMC_LANDMARKS.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.PFMC_LANDMARKS.key, data:{/*layer:efhGeneralPFMCLandmarksMapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.PFMC_LANDMARKS.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.PFMC_LANDMARKS.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.MARINE_PROTECTED_AREAS.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.MARINE_PROTECTED_AREAS.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.MARINE_PROTECTED_AREAS.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.MARINE_PROTECTED_AREAS.key, data:{/*layer:efhGeneralMarinProtectedAreasMapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.MARINE_PROTECTED_AREAS.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.MARINE_PROTECTED_AREAS.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.key, data:{/*layer:efhGeneralEEZMapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.key, data:{/*layer:stateTerritSeaBoundMapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.mapServices}, icon: false}
                    ]},
                  {title: '<a target="_blank" title="EFH Catalog" href="https://www.nwfsc.noaa.gov/data/efh-catalog/">EFH Catalog</a>', folder: false, icon: false,hideCheckbox: true, unselectable:true}
		]},
			{title: FANCYTREE_ITEMS.HOOK_LINE.title, key: FANCYTREE_ITEMS.HOOK_LINE.key, folder: true,  children: [
		  {title: '<a target="_blank" href="metadata/'+FANCYTREE_ITEMS.HOOK_LINE.CATCH.url+'" >'+FANCYTREE_ITEMS.HOOK_LINE.CATCH.title+'</a> <i><a title="Download CSV File"  data-name="'+FANCYTREE_ITEMS.HOOK_LINE.CATCH.key+'" >CSV</a></i>', key: FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, icon: false},
		  {title: '<a target="_blank" href="metadata/'+FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.url+'" >'+FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.title+'</a> <i><a  title="Download CSV File" data-name="'+FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key+'" >CSV</a></i>', key: FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, icon: false},
		  {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.title+'" href="'+FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.url+'" >'+FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.title+'</a>', key: FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.key, data:{/*layer:hookLineSamplingSitesLayer  , */url:FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.url, mapServices:FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.mapServices}, icon: false}
		]},
		{title: FANCYTREE_ITEMS.OBSERVER.title, key: FANCYTREE_ITEMS.OBSERVER.key, folder: true,   unselectable :true, children: [
		  {title: '<a target="_blank" href="metadata/'+FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.url+'" >'+FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.title+'</a> (Download Only) <i><a title="Download CSV File" data-name="'+FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key+'" >CSV</a></i>', key: FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key, icon: false, unselectable :true},
		  {title: '<a target="_blank" href="metadata/'+FANCYTREE_ITEMS.OBSERVER.GEMM.url+'" >'+FANCYTREE_ITEMS.OBSERVER.GEMM.title+'</a> (Download Only) <i><a title="Download CSV File" data-name="'+FANCYTREE_ITEMS.OBSERVER.GEMM.key+'" >CSV</a></i>', key: FANCYTREE_ITEMS.OBSERVER.GEMM.key, icon: false, unselectable :true},
		   {title: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.title, key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.key, icon: false,
		        children: [
		    		{title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2002_2005.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2002_2005.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2002_2005.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2002_2005.key, icon: false, data:{/*layer:atSeaMidTrawlCP2002_2005Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2002_2005.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2002_2005.mapServices}},
		             {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2006_2010.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2006_2010.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2006_2010.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2006_2010.key, icon: false, data:{/*layer:atSeaMidTrawlCP2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2002_2005.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2006_2010.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2011_2015.key, icon: false, data:{/*layer:atSeaMidTrawlCP2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_CP_2011_2015.mapServices}},
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2002_2005.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2002_2005.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2002_2005.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2002_2005.key, icon: false, data:{/*layer:atSeaMidTrawlMS2002_2005Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2002_2005.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2002_2005.mapServices}},
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2006_2010.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2006_2010.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2006_2010.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2006_2010.key, icon: false, data:{/*layer:atSeaMidTrawlMS2006_2010Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2006_2010.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2006_2010.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2011_2015.key, icon: false, data:{/*layer:atSeaMidTrawlMS2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.AT_SEA_MID_TRAWL_MS_2011_2015.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2002_2006.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2002_2006.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2002_2006.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2002_2006.key, icon: false, data:{/*layer:leBottomTrawl2002_2006Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2002_2006.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2002_2006.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2006_2010.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2006_2010.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2006_2010.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2006_2010.key, icon: false, data:{/*layer:leBottomTrawl2006_2010Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2006_2010.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.LE_BOTTOM_TRAWL_2006_2010.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_BOTTOM_TRAWL_2002_2010.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_BOTTOM_TRAWL_2002_2010.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_BOTTOM_TRAWL_2002_2010.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_BOTTOM_TRAWL_2002_2010.key, icon: false, data:{/*layer:csBottomTrawl2002_2010Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_BOTTOM_TRAWL_2002_2010.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_BOTTOM_TRAWL_2002_2010.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2002_2010.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2002_2010.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2002_2010.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2002_2010.key, icon: false, data:{/*layer:nonCSHookLine2002_2010Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2002_2010.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2002_2010.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2011_2015.key, icon: false, data:{/*layer:nonCSHookLine2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_HOOK_LINE_2011_2015.mapServices}},
		             {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_HOOK_LINE_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_HOOK_LINE_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_HOOK_LINE_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_HOOK_LINE_2011_2015.key, icon: false, data:{/*layer:csHookLine2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_HOOK_LINE_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_HOOK_LINE_2011_2015.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2002_2010.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2002_2010.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2002_2010.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2002_2010.key, icon: false, data:{/*layer:nonCSPot2002_2010Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2002_2010.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2002_2010.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2011_2015.key, icon: false, data:{/*layer:nonCSPot2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.NON_CS_POT_2011_2015.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_POT_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_POT_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_POT_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_POT_2011_2015.key, icon: false, data:{/*layer:csPot2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_POT_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.CS_POT_2011_2015.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_HAKE_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_HAKE_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_HAKE_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_HAKE_2011_2015.key, icon: false, data:{/*layer:shoresideMidTrawlHake2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_HAKE_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_HAKE_2011_2015.mapServices}}, 
		            {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_ROCKFISH_2011_2015.tooltip+'" href="'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_ROCKFISH_2011_2015.url+'" >'+FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_ROCKFISH_2011_2015.title+'</a>', key: FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_ROCKFISH_2011_2015.key, icon: false, data:{/*layer:shoresideMidTrawlRockfish2011_2015Layer  , */url:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_ROCKFISH_2011_2015.url, mapServices:FANCYTREE_ITEMS.OBSERVER.FISHING_EFFORT_2002_2015.SHORESIDE_MID_TRAWL_ROCKFISH_2011_2015.mapServices}}

              ]
		   }
		]},

	  {title: FANCYTREE_ITEMS.TRAWL.title, key: FANCYTREE_ITEMS.TRAWL.key, folder: true, children: [
		{title: '<a target="_blank" href="metadata/'+FANCYTREE_ITEMS.TRAWL.CATCH.url+'" >'+FANCYTREE_ITEMS.TRAWL.CATCH.title +'</a> <i><a title="Download CSV File"  data-name="'+FANCYTREE_ITEMS.TRAWL.CATCH.key+'" >CSV</a></i>', key: FANCYTREE_ITEMS.TRAWL.CATCH.key, icon: false},
		{title: '<a target="_blank" href="metadata/'+FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.url+'" >'+FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.title+'</a> <i><a  title="Download CSV File" data-name="'+FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key+'" >CSV</a></i>', key: FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key, icon: false},
		  {title: '<a target="_blank" href="metadata/'+FANCYTREE_ITEMS.TRAWL.SPECIMENS.url+'" >'+FANCYTREE_ITEMS.TRAWL.SPECIMENS.title +'</a> <i><a  title="Download CSV File" data-name="'+FANCYTREE_ITEMS.TRAWL.SPECIMENS.key+'" >CSV</a></i>', key: FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, icon: false},
//		  {title: 'Conf' +' <i><a  title="Download CSV File" data-name="conf" >Conf CSV</a></i>', key: 'conf', icon: false},
		{title: '<a target="_blank" title="'+FANCYTREE_ITEMS.TRAWL.STATION_GRID.title+'" href="'+FANCYTREE_ITEMS.TRAWL.STATION_GRID.url+'" >'+FANCYTREE_ITEMS.TRAWL.STATION_GRID.title+'</a>', key: FANCYTREE_ITEMS.TRAWL.STATION_GRID.key, data:{/*layer:trawlSurveyStationGridLayer  , */url:FANCYTREE_ITEMS.TRAWL.STATION_GRID.url, mapServices:FANCYTREE_ITEMS.TRAWL.STATION_GRID.mapServices}, icon: false}
		]},
		{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.key, folder: true,  children: [
   			 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.key+1000, data:{/*layer:efhGeneralGroundfishTrawlPoly20152016MapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_POLY_2015_2016.mapServices}, icon: false},
			{title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.key+1000, data:{/*layer:efhGeneralGroundfishTrawlLines20152016MapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.GROUNDFISH_TRAWL_RCA_LINES_2015_2016.mapServices}, icon: false},
    	{title: '<a target="_blank" title="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.title+'" href="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.url+'" >'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.title+'</a>', key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.key, data:{/*layer:spatialReferencesMarineProtectedAreasLayer,*/url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.mapServices}, icon: false},

		  {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.title+'" href="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.url+'" >'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.title+'</a>', key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.key, data:{/*layer:spatialReferencesBathymetricCountoursLayer  , */url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.mapServices}, icon: false},
		{title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.key, folder: true,  children: [
                        {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.title+'" href="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.url+'" >'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.title+'</a>', key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.key+1000, data:{ url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1_4_0.mapServices}, icon: false},
                        {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.title+'" href="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.url+'" >'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.title+'</a>', key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.key, data:{url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.mapServices}, icon: false},
                        {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.title+'" href="'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.url+'" >'+FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.title+'</a>', key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.key, data:{ url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.mapServices}, icon: false}
                    ]},
				{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.key, folder: true,  children: [
				 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.title+'" href="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.url+'" >'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.title+'</a>', key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.key, data:{/*layer:spatialReferencesRegulatoryBoundariesPFMCLandmarksLayer,*/url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.mapServices}, icon: false},
			{title: '<a target="_blank" title="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.title+'" href="'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.url+'" >'+FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.title+'</a>', key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.key, data:{/*layer:spatialReferencesRegulatoryBoundariesINPFCAreasLayer , */url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.mapServices}, icon: false},
			 {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.key+1000, data:{/*layer:efhGeneralEEZMapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.ECONOMIC_EXCLUSION_ZONE.mapServices}, icon: false},
                         {title: '<a target="_blank" title="'+FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.title+'" href="'+FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.url+'" >'+FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.title+'</a>', key: FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.key+1000, data:{/*layer:stateTerritSeaBoundMapLayer  , */url:FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.url, mapServices:FANCYTREE_ITEMS.EFH.GENERAL.STATE_TERRIT_SEA_BOUND.mapServices}, icon: false}
				]},
		]}
	  ],
	  checkbox: true,
	  selectMode:3
	});



  // Expand all tree nodes, if leaf is a map layer, add transparency child node
  $("#layers").fancytree("getTree").visit(function(node){

    if(node.data.url!=null )

          node.addChildren({
            title: 'Transparency: <input class="slider-width-custom" id="'+node.key+'"  type="range" min="0" max="1" step="0.01" value="1" >',
            icon: false,
            unselectable :true,
            hideCheckbox: true
          });

  });

  $("#layers").fancytree("getTree").visit(function(node){

    if(node.data.url!=null )
          node.addChildren({
            title: 'Legend: <input style="min-width:0px" id="'+node.key+'"  type="checkbox"  >',
            icon: false,
            unselectable :true,
            hideCheckbox: true
          });


  });

  $("#layers").fancytree("getTree").visit(function(node){

    if(node.data.url!=null )
          node.addChildren({
            title: '<a style="min-width:0px" id="zoom'+node.key+'"   >Zoom to Layer</a>',
            icon: false,
            unselectable :true,
            hideCheckbox: true
          });


  });

    //handle transparency for map service layers
	$( "#layers" ).bind( "mousemove", function( ev ) {
            var opacity = 1;
            var opacityLayer = null;


            if ($(ev.target).closest('input')[0]!=null)
            {
	            opacity = $(ev.target).closest('input')[0].value;
	            opacityLayer = $(ev.target).closest('input')[0].id;

	            if(allLayers[opacityLayer]!=null)
	                allLayers[opacityLayer].setOpacity(opacity);
	        }

	});


    //this function traverses down a json node hierarchy and looks for an object w/ passed in key
    function traverse(jsonObj,findKey) {
        if( typeof jsonObj == "object" ) {


            if(jsonObj.key==findKey)
                foundNode = jsonObj;


            Object.entries(jsonObj).forEach(([key, value]) => {
                // key is either an array index or object key
                traverse(value,findKey);
            });
        }
        else {
            // jsonObj is a number or string
        }
    }

	//get the layer key from CSV and pass it to getCSV function
	//$( "#layers,#layers-content" ).bind( "click", function( ev ) {
	$( "#layers" ).bind( "click", function( ev ) {
			var layer = $(ev.target).closest('a').data('name');
			var legendLayer;
			var zoomLayer;

            if ($(ev.target).closest('input')[0]!=null)
            {
	            legendLayer = $(ev.target).closest('input')[0].id;

	            if(allLayers[legendLayer]!=null && $(ev.target).closest('input')[0].checked)
	            {

                      $.ajax({ url: allLayers[legendLayer].options.url+'legend',
                            success: function(data) {
                                    var legendHTMLResponse = $(data).closest('div.rbody');
                                    if (legendHTMLResponse[0]==null)
                                       legendHTMLResponse =  $(data).closest('div.restBody');

                                //uncheck other checkboxes (can possibly be optimized with jquery built in functions)
                                 for(var i=0; i<$( "input:checkbox" ).length; i++)
                                        if($( "input:checkbox" )[i].id.search("zoom")<0 &&  $( "input:checkbox" )[i].id!=legendLayer)
                                             $( "input:checkbox" )[i].checked=false;

                                    $("#legend").show();
                                    $("#legend-rectangle").show();
                                    $("#legend").height('auto');

                                    if(legendLayer==71)
                                        $("#legend").html(legendHTMLResponse[0].innerHTML.replace(/img src="/g,'img src="'+allLayers[legendLayer].options.url));
                                    else
                                        $("#legend").html(legendHTMLResponse[0].innerHTML);

                                    if ($("#legend").innerHeight()<240)
                                    {
                                        $("#legend-rectangle").height($("#legend").innerHeight()+20);
                                    }
                                    else
                                    {
                                        $("#legend-rectangle").height(270);
                                          $("#legend").height(250);
                                         $("#legend").scroll();
                                    }


                            }
                        });

	            }
	            else
	            {
                    $("#legend").hide();
                    $("#legend-rectangle").hide();
	            }
	        }


            if ($(ev.target)[0]!=null)
            {

	            zoomLayer = $(ev.target)[0].id.substring(4, $(ev.target)[0].id.length);

		        if(allLayers[zoomLayer]!=null)
	            {

                      $.ajax({ url: allLayers[zoomLayer].options.url+'info/iteminfo',
                            success: function(data) {

                           var bounds = $(data).find("td:contains('[[')")[0].innerHTML;
                           var latlngs = JSON.parse( bounds );

                           //arcgis returns long/lat so convert into lat/long then get bounds
                           latlngs[0] = [latlngs[0][1],latlngs[0][0]];
                           latlngs[1] = [latlngs[1][1],latlngs[1][0]];
                           bounds = L.latLngBounds(latlngs);


                            if(bounds!=null)
                                map.flyToBounds(bounds);


                            }
                        });

	            }
	            else
	            {
                    $("#legend").hide();
                    $("#legend-rectangle").hide();
	            }
	        }

//			if(self.selectedSpecies.length == 0 && layer != undefined && layer!=FANCYTREE_ITEMS.OBSERVER.GEMM.key && layer!=FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key && layer!='conf')
//				alert("Please specify at least one species in the Search Filters box above in order to download this layer.");

			getCSV(layer);

	});


	function getCSV(layer){

		var startMonth = self.cycleStartDate.getMonth()+1;
			var startDay = self.cycleStartDate.getDate();

			var endMonth = self.cycleEndDate.getMonth()+1;
			var endDay = self.cycleEndDate.getDate();

			if (startMonth<10)
				startMonth = '0'+startMonth;


			if (startDay<10)
				startDay = '0'+startDay;

			if (endMonth<10)
				endMonth = '0'+endMonth;


			if (endDay<10)
				endDay = '0'+endDay;

			var startDate = (self.cycleStartDate.getMonth()+1)+'/'+self.cycleStartDate.getDate()+'/'+self.cycleStartDate.getFullYear();
			var endDate = (self.cycleEndDate.getMonth()+1)+'/'+self.cycleEndDate.getDate()+'/'+self.cycleEndDate.getFullYear();

			var startDateyyyymmdd = self.cycleStartDate.getFullYear()+''+startMonth+''+startDay;
			var endDateyyyymmdd = self.cycleEndDate.getFullYear()+''+endMonth+''+endDay;

			var j_species_scientific_names = [];

			if (self.selectedSpecies!=null && self.selectedSpecies!='')
			 for (var i = 0; i < self.selectedSpecies.length; i++)
					j_species_scientific_names.push(self.selectedSpecies[i].scientific_name);

			if ( layer==FANCYTREE_ITEMS.TRAWL.CATCH.key && j_species_scientific_names!=null && j_species_scientific_names!='' )
				getTrawlCatchCSV(j_species_scientific_names,startDateyyyymmdd,endDateyyyymmdd);

			if ( layer==FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key  && j_species_scientific_names!=null && j_species_scientific_names!='' )
				getObserverCatchCSV(j_species_scientific_names,startDateyyyymmdd,endDateyyyymmdd);

			if ( layer==FANCYTREE_ITEMS.TRAWL.SPECIMENS.key  && j_species_scientific_names!=null && j_species_scientific_names!='' )
				getTrawlSpecimensCSV(j_species_scientific_names,startDateyyyymmdd,endDateyyyymmdd)

			if ( layer==FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key )
				getTrawlHaulCharsCSV(startDateyyyymmdd,endDateyyyymmdd)

			if ( layer==FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key  && j_species_scientific_names!=null && j_species_scientific_names!='' )
				getHookLineSpecimensCSV(j_species_scientific_names,startDateyyyymmdd,endDateyyyymmdd)

			if ( layer==FANCYTREE_ITEMS.HOOK_LINE.CATCH.key  && j_species_scientific_names!=null && j_species_scientific_names!='' )
				getHookLineCatchCSV(j_species_scientific_names,startDateyyyymmdd,endDateyyyymmdd)

			if ( layer==FANCYTREE_ITEMS.OBSERVER.GEMM.key)
				getGEMMCSV()
				
			if ( layer==FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key) 
				getCatchExpansionsCSV()

			if ( layer=='conf' )
				getConfCSV()
	}




/*********************************************************************************************************************************************
	FancyTree helper functions
**********************************************************************************************************************************************/

	//check the fancy tree checkbox on both groups
	//if set = true, check the box, if set=false, uncheck
    function setFancytreeItem(fancytreeItem, set) {
				$("#layers").off("fancytreeselect");
				$("#layers").fancytree("getTree").getNodeByKey(fancytreeItem.key).setSelected(set);
				$("#layers").on("fancytreeselect", fancyTreeHandler);
	}

/*********************************************************************************************************************************************
	FancyTree layer event handlers/functions
**********************************************************************************************************************************************/

	$("#layers").on("fancytreeselect", fancyTreeHandler);

  //ArcGIS feature
  var identifiedFeature;
  var identifiedFeatureLayer;

  //identify ArcGIS feature and display all properties
  map.on('click', function (e) {

        for (var i=0; i<self.checkedLayers.length;i++)
        {
            if(allLayers[self.checkedLayers[i]]!=undefined)
                allLayers[self.checkedLayers[i]].identify().on(map).at(e.latlng).run(function(error, featureCollection){
                    displayArcGISfields(featureCollection,self.checkedLayers[i]);
                });
        }

  });

	//This function retrieves ArcGIS fields and
	//displays them as a marker on the map
	function displayArcGISfields(featureCollection, key){
        if (featureCollection!=null)
        {
            if(identifiedFeature){
              map.removeLayer(identifiedFeature);
            }

            identifiedFeatureLayer = key;

             if (featureCollection.features.length > 0) {

                    var bindHTML = '<table  class="display" cellspacing="0" cellpadding="5">'
                    +'        <thead align="left">'
                    +'            <tr class="metadataHeader">'
                    +'                <th>Field&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
                    +'                <th>Value&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
                    +'            </tr>'
                    +'        </thead>'
                    +'        <tbody>';


                    var i=0;

                    for (var prop in featureCollection.features[0].properties) {
                      if(i%2==0)
                        bindHTML +='<tr class="metadataEven"><td>'+prop+'&nbsp;&nbsp;&nbsp;</td><td>'+featureCollection.features[0].properties[prop]+'</td></tr>';
                      else
                        bindHTML +='<tr class="metadataOdd"><td>'+prop+'&nbsp;&nbsp;&nbsp;</td><td>'+featureCollection.features[0].properties[prop]+'</td></tr>';

                      i++;

                    }

                    bindHTML +='</tbody></table>';

                    identifiedFeature = L.geoJson(featureCollection.features[0]).addTo(map).bindPopup(bindHTML,{'minWidth': '100%'}).openPopup();

              }
        }
	}


	//This function shows/hides ArcGIS layers based on
	//fancytree item keys and their corresponding data property
	function fancyTreeArcGISHandler(node){

		if( node.data.url )
			{
				if( node.isSelected()	 )
				{

					setFancytreeItem(node,true);

					if( node.data.layer  != null )
						 map.addLayer(node.data.layer );
					else
					{
                        L.esri.request(node.data.url, {}, function (error, response) {

                                if (response.singleFusedMapCache) {
                                       console.log("tiledMapLayer");
                                       node.data.layer = L.esri.tiledMapLayer({
                                            url: node.data.url,
                                            pane: 'custom',
                                            useCors: false,
                                            zIndex:1
                                        });

//                                        console.log(node.data.layer);


                                } else {
                                        console.log("dynamicMapLayer");

                                        node.data.layer = L.esri.dynamicMapLayer({
                                          url: node.data.url,
                                          layers: node.data.mapServices,
                                          opacity : 1,
                                           pane: 'custom',
                                            useCors: false,
                                            zIndex:1
                                        });

                                }

                                map.addLayer(node.data.layer);

                                //store the layer in an array w/ index of layer key for reuse
                                allLayers[node.key] = node.data.layer;
                    });




					}

					if( self.checkedLayers.indexOf(node.key) < 0 )
						self.checkedLayers.push(node.key);

				}
				else if ( self.checkedLayers.indexOf(node.key) > -1 )
				{
					setFancytreeItem(node,false);
					map.removeLayer(node.data.layer);
					self.checkedLayers.splice(self.checkedLayers.indexOf(node.key), 1);

					//remove ArcGIS feature marker if layer is unchecked
					if(identifiedFeatureLayer==node.key)
					{
						map.removeLayer(identifiedFeature);
					}

				}

		}
		else if(node.children != null)
		{

			for(var i=0;i<node.children.length;i++)
				fancyTreeArcGISHandler(node.children[i]); //note recursive call
		}

	}

	function fancyTreeHandler(event, data){

	//start spinner
    spinner.spin(target);

	//set timeout for handling of heavy javascript calls
	setTimeout(function() {


		var startMonth = self.cycleStartDate.getMonth()+1;
			var startDay = self.cycleStartDate.getDate();

			var endMonth = self.cycleEndDate.getMonth()+1;
			var endDay = self.cycleEndDate.getDate();

			if (startMonth<10)
				startMonth = '0'+startMonth;


			if (startDay<10)
				startDay = '0'+startDay;

			if (endMonth<10)
				endMonth = '0'+endMonth;


			if (endDay<10)
				endDay = '0'+endDay;

			var startDate = (self.cycleStartDate.getMonth()+1)+'/'+self.cycleStartDate.getDate()+'/'+self.cycleStartDate.getFullYear();
			var endDate = (self.cycleEndDate.getMonth()+1)+'/'+self.cycleEndDate.getDate()+'/'+self.cycleEndDate.getFullYear();

			var startDateyyyymmdd = self.cycleStartDate.getFullYear()+''+startMonth+''+startDay;
			var endDateyyyymmdd = self.cycleEndDate.getFullYear()+''+endMonth+''+endDay;

			//handle ArcGIS layers
			//assumption is that it will be an ArcGIS layer (must update in the future if not using ArcGIS)
			fancyTreeArcGISHandler(data.node);


			if ( data.node.key==FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key || data.node.key==FANCYTREE_ITEMS.HOOK_LINE.key )
			{


				if( data.node.isSelected()	 )
				{
					hookLineSpecimenCanceler = $q.defer();


					setFancytreeItem(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS,true);


					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key);

						var j_species_codes = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++)
								j_species_codes.push(self.selectedSpecies[i].scientific_name);
						else
						    alert("Please specify at least one species in the Search Filters box above in order to download this layer.");


						getPlotHookLineSpecimens(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key) > -1 )
				{

						hookLineSpecimenCanceler.resolve();


						layerUncheckCleanup(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS);


				}

			}


			if ( data.node.key==FANCYTREE_ITEMS.HOOK_LINE.CATCH.key || data.node.key==FANCYTREE_ITEMS.HOOK_LINE.key )
			{
				if( data.node.isSelected()	 )
				{
					hookLineCatchCanceler = $q.defer();

					setFancytreeItem(FANCYTREE_ITEMS.HOOK_LINE.CATCH,true);


					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key);

						var j_species_codes = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++)
								j_species_codes.push(self.selectedSpecies[i].scientific_name);
						else
						    alert("Please specify at least one species in the Search Filters box above in order to download this layer.");

						getPlotHookLineCatch(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key) > -1 )
				{
						hookLineCatchCanceler.resolve();

						layerUncheckCleanup(FANCYTREE_ITEMS.HOOK_LINE.CATCH);

				}

			}


			if ( data.node.key==FANCYTREE_ITEMS.TRAWL.SPECIMENS.key || data.node.key==FANCYTREE_ITEMS.TRAWL.key )
			{
				if( data.node.isSelected()	 )
				{
					 trawlSpecimensCanceler = $q.defer();


					setFancytreeItem(FANCYTREE_ITEMS.TRAWL.SPECIMENS,true);


					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key);

						var j_species_codes = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++)
								j_species_codes.push(self.selectedSpecies[i].scientific_name);
						else
						    alert("Please specify at least one species in the Search Filters box above in order to download this layer.");

						getPlotTrawlSpecimens(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key) > -1 )
				{
					trawlSpecimensCanceler.resolve();


					layerUncheckCleanup(FANCYTREE_ITEMS.TRAWL.SPECIMENS);


				}//end if( data.node.isSelected() )

			} //end if (data.node.title=='Individual Organisms' || data.node.title=='Trawl')



			if (data.node.key==FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key || data.node.key==FANCYTREE_ITEMS.TRAWL.key)
			{
				if( data.node.isSelected() )
				{

					trawlHaulCharsCanceler = $q.defer();

					setFancytreeItem(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS,true);


					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key);
						getPlotTrawlHaulChars(startDateyyyymmdd,endDateyyyymmdd);
					}
				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key) > -1 )
				{
					trawlHaulCharsCanceler.resolve();

					layerUncheckCleanup(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS);


				}//end if( data.node.isSelected() )

			} //end if (data.node.title==FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key || data.node.title=='Trawl')



			if ( data.node.key==FANCYTREE_ITEMS.TRAWL.CATCH.key || data.node.key==FANCYTREE_ITEMS.TRAWL.key )
			{
				if( data.node.isSelected()	 )
				{

					trawlCatchCanceler = $q.defer();

					setFancytreeItem(FANCYTREE_ITEMS.TRAWL.CATCH,true);

					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.CATCH.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.TRAWL.CATCH.key);

						var j_species_scientific_names = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++)
								j_species_scientific_names.push(self.selectedSpecies[i].scientific_name);
						else
						    alert("Please specify at least one species in the Search Filters box above in order to download this layer.");

						getPlotTrawlCatch(j_species_scientific_names,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.CATCH.key) > -1 )
				{


					trawlCatchCanceler.resolve();

					layerUncheckCleanup(FANCYTREE_ITEMS.TRAWL.CATCH);


				}//end if( data.node.isSelected() )

			} //end if (data.node.title==FANCYTREE_ITEMS.TRAWL.CATCH.key || data.node.title=='Trawl')


		//stop spinner
		spinner.stop();
	  }, 10); // end setTimeout required for showing spinner during heavy javascript calls

	}



   /**
     * Clean up data after a layer has been unchecked
     */
    function layerUncheckCleanup(fancyTreeItem) {

		//remove the FancyTree item from the checked layers
		self.checkedLayers.splice(self.checkedLayers.indexOf(fancyTreeItem.key), 1);

		//remove all point primitives from the map
		showHideMarkers(fancyTreeItem.key, null, false);

		//uncheck the corresponding group layer
		setFancytreeItem(fancyTreeItem,false);

	}


/*********************************************************************************************************************************************
	Show/hide marker function
**********************************************************************************************************************************************/


    /**
     * Check if an existing species markers data exists for a particular layer to avoid an API call.
	 * If show = true, then the points are shown, otherwise, the points are hidden
	 * returns the true if layer/species combination exists, otherwise returns false
     */
	function showHideMarkers(layer, scientificName, show){
		var markerExists = false;
		var speciesNoBlanks = null;

		if( scientificName!= null)
			speciesNoBlanks = (scientificName).replace(/\s+/g, '');

		if( !show && layerToPrimitiveDict.has(layer) )
		{
			if( layerToPrimitiveDict.get(layer).has(speciesNoBlanks) )
			{

				//remove layer from the map
				map.removeLayer( layerToPrimitiveDict.get(layer).get(speciesNoBlanks));
				markerExists = true;

			}
			else if ( speciesNoBlanks == null )
			{
				var layerSpeciesIndices = layerToPrimitiveDict.get(layer);
				for(var i=0; i<layerSpeciesIndices.keys.length; i++)
				{

					var speciesIndex = layerToPrimitiveDict.get(layer).values[i];

					map.removeLayer( layerToPrimitiveDict.get(layer).values[i]);

				}

			}
		}


		//in case of Trawl Haul chars, the species 2nd hashmap
		//has only one key and that is FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key
		if(layer==FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key && !speciesNoBlanks)
			speciesNoBlanks = FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key;

		if(show && layerToPrimitiveDict.has(layer) )
		{

			if( layerToPrimitiveDict.get(layer).has(speciesNoBlanks) )
			{
				markerExists = true;

				var cluster = layerToPrimitiveDict.get(layer).get(speciesNoBlanks);
				map.addLayer(cluster);

			}

		}


		return markerExists;
	}





/*********************************************************************************************************************************************
	Handle species chip add/remove
**********************************************************************************************************************************************/



	$scope.$watchCollection('ctrl.selectedSpecies', function(newNames, oldNames) {

			var species_codes = [];
			var scientific_names = [];
			var removed_map_points = [];

			var removed_species = $(oldNames).not(newNames).get();  //species that were removed
			var added_species = $(newNames).not(oldNames).get()		//species that were added

			var startMonth = self.cycleStartDate.getMonth()+1;
			var startDay = self.cycleStartDate.getDate();

			var endMonth = self.cycleEndDate.getMonth()+1;
			var endDay = self.cycleEndDate.getDate();

			if (startMonth<10)
				startMonth = '0'+startMonth;


			if (startDay<10)
				startDay = '0'+startDay;

			if (endMonth<10)
				endMonth = '0'+endMonth;


			if (endDay<10)
				endDay = '0'+endDay;


			var startDateyyyymmdd = self.cycleStartDate.getFullYear()+''+startMonth+''+startDay;
			var endDateyyyymmdd = self.cycleEndDate.getFullYear()+''+endMonth+''+endDay;

			if (self.cycleStartDate!=null)
				j_cycleStartDate = (self.cycleStartDate.getMonth()+1)+'/'+self.cycleStartDate.getDate()+'/'+self.cycleStartDate.getFullYear();
			if (self.cycleEndDate!=null)
				j_cycleEndDate = (self.cycleEndDate.getMonth()+1)+'/'+self.cycleEndDate.getDate()+'/'+self.cycleEndDate.getFullYear();


			//create an array of the species that were added (used to query DB)
			if (added_species!=null && added_species!='')
				 for (var i = 0; i < added_species.length; i++)
				 {
						//species_codes.push(added_species[i].species_code);
						species_codes.push(added_species[i].scientific_name);
						//scientific_names.push(added_species[i].scientific_name);
				 }

			//get map points of removed species
			if (removed_species!=null && removed_species!='')
			{
				//loop through removed species
				for (var i = 0; i < removed_species.length; i++)
				{


					var newSpeciesNoBlanks = (removed_species[i].scientific_name).replace(/\s+/g, '');
					var index =  '.'+newSpeciesNoBlanks;

					showHideMarkers(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key,removed_species[i].scientific_name,false);
					showHideMarkers(FANCYTREE_ITEMS.TRAWL.CATCH.key,removed_species[i].scientific_name,false);
					showHideMarkers(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key,removed_species[i].scientific_name,false);
					showHideMarkers(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key,removed_species[i].scientific_name,false);


				}
			}

			//start spinner
			spinner.spin(target);

			//set timeout for handling of heavy javascript calls
			setTimeout(function() {

				getPlotTrawlSpecimens(species_codes,startDateyyyymmdd,endDateyyyymmdd);
				getPlotTrawlCatch(species_codes,startDateyyyymmdd,endDateyyyymmdd);
				getPlotHookLineSpecimens(species_codes,startDateyyyymmdd,endDateyyyymmdd);
				getPlotHookLineCatch(species_codes,startDateyyyymmdd,endDateyyyymmdd);

			//stop spinner
			spinner.stop();
		  }, 10); // end setTimeout required for showing spinner during heavy javascript calls


	}); //end $scope.$watchCollection


/*********************************************************************************************************************************************
	Species chip initialization / functions
**********************************************************************************************************************************************/
    /**
     * Search for species.
     */
    function querySearch (query) {

      var results =  [];

      if(self.species != null)
		results = query ? self.species.filter(createFilterFor(query)) : [];

      return results;
    }

    /**
     * Create filter function for a query string
     */
    function createFilterFor(query) {
      var lowercaseQuery = angular.lowercase(query);

      return function filterFn(species) {
        return (species._lowername.indexOf(lowercaseQuery) >= 0) ||
            (species._lowertype.indexOf(lowercaseQuery) >= 0);
      };

    }

    /**
     * Return a map of loaded species
     */
    function loadSpecies(data) {
      var species = data;

      return species.map(function (specie) {
        specie._lowername = '';
		specie._lowertype = '';

		if (specie.common_name!=null)
			specie._lowername = specie.common_name.toLowerCase();
		if (specie.scientific_name!=null)
			specie._lowertype = specie.scientific_name.toLowerCase();


        return specie;
      });
    }


	$http.get(api_base_uri+'/api/v1/source/warehouse.taxonomy_dim/selection.csv?variables=common_name,scientific_name').success(function(csv){

		var jsonArray = CSV2JSON(csv);
		var data = JSON.parse( jsonArray );

		if(data[data.length-1].trawl_id===undefined)
			data.pop();

		self.species = loadSpecies(data);
		$scope.disableSpeciesFilter = false;
	 });


/*********************************************************************************************************************************************
	Login functionality
**********************************************************************************************************************************************/


  $scope.showAdd = function(ev) {


   $http.get(api_base_uri+'/api/v1/user')
            .success(function (data, status, headers, config) {

				if ( data.user.description == 'Authenticated user.')
				{
					    $mdDialog.show({
						  controller: DialogController,
						  template: '<md-dialog aria-label="Logout"><div class="md-dialog-actions" layout="row"> <span flex></span> <md-button ng-click="answer(\'not useful\')"> Cancel </md-button> <md-button ng-click="logout()" class="md-primary"> Logout </md-button> </div></md-dialog>',
						  targetEvent: ev,
						});
				}
				else
				{
					    $mdDialog.show({
						  controller: DialogController,
						  template: '<md-dialog aria-label="Login"><md-content class="md-padding"><div layout=row><div style="position:relative;transform:translateY(12pt)">Click to login: </div><div><md-button ng-href="https://sso-dev.lb.csp.noaa.gov/openam/saml2/jsp/idpSSOInit.jsp?spEntityID='+api_base_uri+'/api/v1/saml/metadata/&metaAlias=/noaa-online/noaa-online-idp&RelayState='+api_base_uri+'/">Login with CAC</md-button><md-button ng-href="https://sso-dev.lb.csp.noaa.gov:8443/openam/saml2/jsp/idpSSOInit.jsp?spEntityID='+api_base_uri+'/api/v1/saml/metadata/&metaAlias=/noaa-online/noaa-online-idp&RelayState='+api_base_uri+'/">Login with NOAA user password</md-button></div></div><br/>(When prompted, select NOAA "ID" certificate - Do not use "Email" certificate)<p/>External Users: <md-button ng-click="showPasswordLoginDialog($event)">Login with User name</md-button><p/><sub>For data access & Non-Disclosure Agreements, contact: <a href="mailto:nwfsc.fram.data@noaa.gov">FRAM data team &lt;nwfsc.fram.data@noaa.gov&gt;</a></sub></md-content></md-dialog>',
						  targetEvent: ev,
						});
				}


            });


  };



function DialogController($scope, $mdDialog) {
  $scope.hide = function() {
    $mdDialog.hide();
  };
  $scope.cancel = function() {
    $mdDialog.cancel();
  };
  $scope.answer = function(answer) {
    $mdDialog.hide(answer);
  };
  $scope.login_provider = {
    options: [
      {id: 'ldap', name: '@noaa.gov'},
      {id: 'external', name: 'Warehouse Account'}
    ]
  };
  $scope.showPasswordLoginDialog = function(ev) {
    $mdDialog.show({
      controller: DialogController,
      template:
        '<md-dialog>' +
        '  <md-content class="md-padding">' +
        '    <h2>Login</h2>' +
        '    <font color="red">{{loginError}}</font><font color="green">{{loginSuccess}}</font>' +
        '    <div layout="row">' +
        '      Select Service Provider:' +
        '    </div>' +
        '    <form name="userForm">' +
        '      <div layout layout-sm="column">' +
        '        <md-input-container flex>' +
        '          <label>Username</label>' +
        '          <input ng-model="dw_uname" >' +
        '        </md-input-container>' +
        '        <md-input-container flex>' +
        '          <label>Service Provider</label>' +
        '          <div layout="row" style="position:relative;transform:translateY(-15pt)">' +
        '            <md-select ng-model="login_provider.selected" ng-model-options="{trackBy: \'$value.id\'}" placeholder="Service Provider">' +
        '              <md-option ng-value="option" ng-repeat="option in login_provider.options">{{option.name}}</md-option>' +
        '            </md-select>' +
        '          </div>' +
        '        </md-input-container>' +
        '      </div>' +
        '      <div layout="row">' +
        '        <md-input-container flex>' +
        '          <label>Password</label>' +
        '          <input type="password" ng-model="dw_pw">' +
        '        </md-input-container>' +
        '      </div>' +
        '    </form>' +
        '    <div layout="row">' +
        '      <a href="'+register_base_uri+'/realms/master/protocol/openid-connect/registrations?response_type=code&client_id=warehouse-dev-bjv">Register New Warehouse Account</a>' +
        '    </div>' +
        '  </md-content>' +
        '  <div class="md-dialog-actions" layout="row">' +
        '    <span flex></span>' +
        '    <md-button ng-click="answer(\'not useful\')"> Cancel </md-button>' +
        '    <md-button ng-click="login()" class="md-primary"> Login </md-button>' +
        '  </div>' +
        '</md-dialog>',
      targetEvent: ev,
      clickOutsideToClose: true
    });
  };

    $scope.logout = function() {

		$http.get(api_base_uri+'/api/v1/logout',{
			  ignoreLoadingBar: true
			});
		 $mdDialog.hide();

	}

    $scope.login = function() {

	    // use $.param jQuery function to serialize data from JSON
            var data = $.param({
                username: $scope.dw_uname,
                password: $scope.dw_pw
            });

              var config = {
                headers : {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'
                }
            }

            // check which login API to use
            if ($scope.login_provider.selected.id === 'external') {
                var login_url = api_base_uri+'/api/v1/external/login';
            } else {
                var login_url = api_base_uri+'/api/v1/login';
            }

            $http.post(login_url, data, config)
            .success(function (data, status, headers, config) {
				$scope.loginError = "";
                $scope.loginSuccess =  "Logged in successfully";
				$mdDialog.hide();


            })
            .error(function (data, status, header, config) {
				$scope.loginSuccess = "";
                $scope.loginError =  data.error;

            });


  };
};


/*********************************************************************************************************************************************
	Functions for API calls
**********************************************************************************************************************************************/

    /**
     * Get haul characteristics data from DB and plot points based on input parameters
     */
    function getPlotTrawlHaulChars(j_cycleStartDate,j_cycleEndDate) {
		var get_stmt = api_base_uri+'/api/v1/source/trawl.operation_haul_fact/selection.csv?variables=date_yyyymmdd,sampling_start_hhmmss,sampling_end_hhmmss,project,vessel,pass,leg,trawl_id,performance,latitude_dd,longitude_dd,vessel_start_latitude_dd,vessel_start_longitude_dd,vessel_end_latitude_dd,vessel_end_longitude_dd,gear_start_latitude_dd,gear_start_longitude_dd,gear_end_latitude_dd,gear_end_longitude_dd,area_swept_ha_der,net_height_m_der,net_width_m_der,door_width_m_der,temperature_at_gear_c_der,temperature_at_surface_c_der,depth_hi_prec_m,turbidity_ntu_der,salinity_at_gear_psu_der,o2_at_gear_ml_per_l_der,vertebrate_weight_kg,invertebrate_weight_kg,nonspecific_organics_weight_kg,fluorescence_at_surface_mg_per_m3_der';

		if( haulCharDataSourceStartDt==j_cycleStartDate && haulCharDataSourceEndDt==j_cycleEndDate )
			showHideMarkers(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key,null,true);
		else
		{

			showHideMarkers(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key,null,false);

			//store the dates so if a user checks/unchecks
			//the Trawl Haul Chars layer, we don't have to
			//make an API call as layer is not species specific
			haulCharDataSourceStartDt = j_cycleStartDate;
			haulCharDataSourceEndDt = j_cycleEndDate;

			$http.get(get_stmt,{ timeout: trawlHaulCharsCanceler.promise, params: {filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{

				var jsonArray = CSV2JSON(csv);
				csv = null;
				var data = JSON.parse( jsonArray );

				if(data[data.length-1].trawl_id===undefined)
					data.pop();

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key, new Dict() );


				var el;
				var i=0;

				//Trawl Haul Chars will use the same layer to primitive hashmap
				//but instead of having the 2nd hashmap key off species, we just passing in a dummy string
				//where the dummy string = FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key
				layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).set(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key , L.markerClusterGroup());

				while (el = data.shift()) {


					setRandomMapColor(el.vessel);
					var marker = L.ExtraMarkers.icon({ icon: 'glyphicon-asterisk', markerColor: randomColor.get(el.vessel)});

					var bindHTML = '<table  class="display" cellspacing="0" cellpadding="5">'
					+'        <thead align="left">'
					+'            <tr class="metadataHeader">'
					+'                <th>Field&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
					+'                <th>Value&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
					+'            </tr>'
					+'        </thead>'
					+'        <tbody>';

					bindHTML +='<tr class="metadataEven"><td>Date-Time (YYYYmmdd)&nbsp;&nbsp;&nbsp;</td><td>'+el.date_yyyymmdd+'</td></tr>'
					+'<tr class="metadataOdd"><td>Sampling Start Time (HHMMSS)&nbsp;&nbsp;&nbsp;</td><td>'+el.sampling_start_hhmmss+'</td></tr>'
					+'<tr class="metadataEven"><td>Sampling End Time (HHMMSS)nbsp;&nbsp;&nbsp;</td><td>'+el.sampling_end_hhmmss+'</td></tr>'
					+'<tr class="metadataOdd"><td>Project&nbsp;&nbsp;&nbsp;</td><td>'+el.project+'</td></tr>'
					+'<tr class="metadataEven"><td>Vessel&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel+'</td></tr>'
					+'<tr class="metadataOdd"><td>Pass&nbsp;&nbsp;&nbsp;</td><td>'+el.pass+'</td></tr>'
					+'<tr class="metadataEven"><td>Leg&nbsp;&nbsp;&nbsp;</td><td>'+el.leg+'</td></tr>'
					+'<tr class="metadataEven"><td>Haul ID&nbsp;&nbsp;&nbsp;</td><td>'+el.trawl_id+'</td></tr>'
					+'<tr class="metadataOdd"><td>Haul Performance&nbsp;&nbsp;&nbsp;</td><td>'+el.performance+'</td></tr>'
					+'<tr class="metadataEven"><td>Haul Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.latitude_dd+'</td></tr>'
					+'<tr class="metadataOdd"><td>Haul Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.longitude_dd+'</td></tr>'
					+'<tr class="metadataEven"><td>Vessel Start Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel_start_latitude_dd+'</td></tr>'
					+'<tr class="metadataOdd"><td>Vessel Start Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel_start_longitude_dd+'</td></tr>'
					+'<tr class="metadataOdd"><td>Vessel End Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel_end_latitude_dd+'</td></tr>'
					+'<tr class="metadataEven"><td>Vessel End Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel_end_longitude_dd+'</td></tr>'
					+'<tr class="metadataOdd"><td>Gear Start Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.gear_start_latitude_dd+'</td></tr>'
					+'<tr class="metadataEven"><td>Gear Start Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.gear_start_longitude_dd+'</td></tr>'
					+'<tr class="metadataOdd"><td>Gear End Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.gear_end_latitude_dd+'</td></tr>'
					+'<tr class="metadataEven"><td>Gear End Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.gear_end_longitude_dd+'</td></tr>'
					+'<tr class="metadataOdd"><td>Area Swept (ha)&nbsp;&nbsp;&nbsp;</td><td>'+el.area_swept_ha_der+'</td></tr>'
					+'<tr class="metadataEven"><td>Net Height (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.net_height_m_der+'</td></tr>'
					+'<tr class="metadataOdd"><td>Net Width (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.net_width_m_der+'</td></tr>'
					+'<tr class="metadataEven"><td>Door Width (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.door_width_m_der+'</td></tr>'
					+'<tr class="metadataOdd"><td>Temperate at Gear (c)&nbsp;&nbsp;&nbsp;</td><td>'+el.temperature_at_gear_c_der+'</td></tr>'
					+'<tr class="metadataEven"><td>Temperature at Surface (c)&nbsp;&nbsp;&nbsp;</td><td>'+el.temperature_at_surface_c_der+'</td></tr>'
					+'<tr class="metadataOdd"><td>Sea Floor Depth (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.depth_hi_prec_m+'</td></tr>'
					+'<tr class="metadataEven"><td>Turbitity (ntu)&nbsp;&nbsp;&nbsp;</td><td>'+el.turbidity_ntu_der+'</td></tr>'
					+'<tr class="metadataOdd"><td>Salinity at Gear (psu)&nbsp;&nbsp;&nbsp;</td><td>'+el.salinity_at_gear_psu_der+'</td></tr>'
					+'<tr class="metadataEven"><td>Dissolved Oxygen (ml/l)&nbsp;&nbsp;&nbsp;</td><td>'+el.o2_at_gear_ml_per_l_der+'</td></tr>'
					+'<tr class="metadataOdd"><td>Vertebrate Weight (kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.vertebrate_weight_kg+'</td></tr>'
					+'<tr class="metadataEven"><td>Invertebrate Weight (kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.invertebrate_weight_kg+'</td></tr>'
					+'<tr class="metadataOdd"><td>Non-specific Organics Weight (kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.nonspecific_organics_weight_kg+'</td></tr>'
					+'<tr class="metadataEven"><td>Fluorescence at Surface (mg/m^3)&nbsp;&nbsp;&nbsp;</td><td>'+el.fluorescence_at_surface_mg_per_m3_der+'</td></tr>'
					;

					bindHTML +='</tbody></table>';

                    if(el.latitude_dd!=null && el.longitude_dd!=null)
					    layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).addLayer(L.marker(L.latLng(el.latitude_dd,el.longitude_dd), { title: el.vessel , icon: marker}).bindPopup(bindHTML));


					i++;



				}; //end while loop

				map.addLayer(layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).get( FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key ));


			}); //end $http.get
		}// end else
	}





    /**
     * Get hook and line specimens data from DB and plot points based on input parameters
     */
    function getPlotHookLineSpecimens(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/hooknline.individual_hooknline_view/selection.csv?variables=project,leg,date_dim$full_date,drop_time_dim$hh24miss,scientific_name,common_name,vessel,site_dim$area_name,site_dim$site_number,drop_latitude_dim$latitude_in_degrees,drop_longitude_dim$longitude_in_degrees,drop_sounder_depth_dim$depth_meters,hook_dim$hook_number,hook_dim$hook_result,sex_dim$sex,length_cm,age_years,weight_kg,otolith_number,fin_clip_number,tow,project_cycle';
		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, self.checkedLayers) >= 0)
			 showSpecies= true;

		var existingHookLineSpecimenData;
		var newSpecies = [];

		for(var i=0;i<j_species_codes.length;i++)
		{
			existingHookLineSpecimenData = showHideMarkers(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key,j_species_codes[i],showSpecies);

			if (!existingHookLineSpecimenData)
				newSpecies.push(j_species_codes[i]);
		}


		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{

			$http.get(get_stmt,{timeout: hookLineSpecimenCanceler.promise, params: {scientific_name:newSpecies,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{


				var newHookLineSpecimenDataSources = new Dict();
				var newHookLineSpecimenDataSource;

				var jsonArray = CSV2JSON(csv);
				csv = null;
				var data = JSON.parse( jsonArray );

				if(data[data.length-1].taxonomy_dim$scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, new Dict() );

				var el;
				while (el = data.shift()) {
					var newSpeciesNoBlanks = (el.scientific_name).replace(/\s+/g, '');


					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).has( newSpeciesNoBlanks ) )
						layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).set(newSpeciesNoBlanks , L.markerClusterGroup());

					setRandomMapColor(newSpeciesNoBlanks);
					var marker = L.ExtraMarkers.icon({ icon: 'glyphicon-asterisk', markerColor: randomColor.get(newSpeciesNoBlanks)});



					if( el.weight_kg>0 )
					{
						var bindHTML = '<table  class="display" cellspacing="0" cellpadding="5">'
						+'        <thead align="left">'
						+'            <tr class="metadataHeader">'
						+'                <th>Field&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'                <th>Value&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'            </tr>'
						+'        </thead>'
						+'        <tbody>';

						bindHTML +='<tr class="metadataEven"><td>Project&nbsp;&nbsp;&nbsp;</td><td>'+el.project+'</td></tr>'
						+'<tr class="metadataOdd"><td>Leg&nbsp;&nbsp;&nbsp;</td><td>'+el.leg+'</td></tr>'
						+'<tr class="metadataEven"><td>Date (YYYYMMDD)&nbsp;&nbsp;&nbsp;</td><td>'+el.date_dim$full_date+'</td></tr>'
						+'<tr class="metadataOdd"><td>Drop Time (HHMMSS)&nbsp;&nbsp;&nbsp;</td><td>'+el.drop_time_dim$hh24miss+'</td></tr>'
						+'<tr class="metadataEven"><td>Scientific Name&nbsp;&nbsp;&nbsp;</td><td>'+el.scientific_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Common Name&nbsp;&nbsp;&nbsp;</td><td>'+el.common_name+'</td></tr>'
						+'<tr class="metadataEven"><td>Vessel&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel+'</td></tr>'
						+'<tr class="metadataEven"><td>Area&nbsp;&nbsp;&nbsp;</td><td>'+el.site_dim$area_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Site Number&nbsp;&nbsp;&nbsp;</td><td>'+el.site_dim$site_number+'</td></tr>'
						+'<tr class="metadataEven"><td>Drop Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.drop_latitude_dim$latitude_in_degrees+'</td></tr>'
						+'<tr class="metadataOdd"><td>Drop Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.drop_longitude_dim$longitude_in_degrees+'</td></tr>'
						+'<tr class="metadataEven"><td>Drop Depth (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.drop_sounder_depth_dim$depth_meters+'</td></tr>'
						+'<tr class="metadataOdd"><td>Hook Number&nbsp;&nbsp;&nbsp;</td><td>'+el.hook_dim$hook_number+'</td></tr>'
						+'<tr class="metadataOdd"><td>Hook Result&nbsp;&nbsp;&nbsp;</td><td>'+el.hook_dim$hook_result+'</td></tr>'
						+'<tr class="metadataEven"><td>Sex&nbsp;&nbsp;&nbsp;</td><td>'+el.sex_dim$sex+'</td></tr>'
						+'<tr class="metadataOdd"><td>Length (cm)&nbsp;&nbsp;&nbsp;</td><td>'+el.length_cm+'</td></tr>'
						+'<tr class="metadataEven"><td>Age&nbsp;&nbsp;&nbsp;</td><td>'+el.age_years+'</td></tr>'
						+'<tr class="metadataOdd"><td>Weight (kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.weight_kg+'</td></tr>'
						+'<tr class="metadataEven"><td>Otolith Number&nbsp;&nbsp;&nbsp;</td><td>'+el.otolith_number+'</td></tr>'
						+'<tr class="metadataOdd"><td>Fin Clip Number&nbsp;&nbsp;&nbsp;</td><td>'+el.fin_clip_number+'</td></tr>'
						;



						bindHTML +='</tbody></table>';
                        if(el.drop_latitude_dim$latitude_in_degrees!=null && el.drop_longitude_dim$longitude_in_degrees!=null)
						    layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).get(newSpeciesNoBlanks).addLayer(L.marker(L.latLng(el.drop_latitude_dim$latitude_in_degrees,el.drop_longitude_dim$longitude_in_degrees), { title: el.scientific_name , icon: marker}).bindPopup(bindHTML));
					}



				}; //end for loop


			while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).has(newSpeciesNoBlanks))
						map.addLayer(layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).get( newSpeciesNoBlanks ));
			}


			}); //end $http.get


		} // end dataSourceExistsBySpecies else condition
    }








    /**
     * Get hook and line catch data from DB and plot points based on input parameters
     */
    function getPlotHookLineCatch(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/hooknline.catch_hooknline_view/selection.csv?variables=project_name,leg,date_dim$full_date,scientific_name,common_name,vessel,site_dim$site_latitude_dd,site_dim$site_longitude_dd,total_catch_numbers,total_catch_wt_kg,site_dim$area_name,site_dim$site_number,wave_height_m,swell_direction_mag,swell_height_m,sea_surface_temp_c,ctd_sounder_depth_m,ctd_on_bottom_measure_depth_dim$depth_meters,ctd_on_bottom_temp_c,ctd_on_bottom_salinity_psu,ctd_on_bottom_disolved_oxygen_sbe43_ml_per_l,ctd_on_bottom_disolved_oxygen_aanderaa_ml_per_l';

		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, self.checkedLayers) >= 0)
			 showSpecies= true;

		var existingHookLineCatchData;
		var newSpecies = [];

		for(var i=0;i<j_species_codes.length;i++)
		{
			existingHookLineCatchData = showHideMarkers(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key,j_species_codes[i],showSpecies);

			if (!existingHookLineCatchData)
				newSpecies.push(j_species_codes[i]);
		}

		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{

			$http.get(get_stmt,{timeout: hookLineCatchCanceler.promise, params: {scientific_name:newSpecies,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{


				var newHookLineCatchDataSources = new Dict();
				var newHookLineCatchDataSource;

				var jsonArray = CSV2JSON(csv);
				csv = null;
				var data = JSON.parse( jsonArray );

				if(data[data.length-1].scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, new Dict() );

				var el;

				while (el = data.shift()) {

					var newSpeciesNoBlanks = (el.scientific_name).replace(/\s+/g, '');

					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).has( newSpeciesNoBlanks ) )
						layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).set(newSpeciesNoBlanks , L.markerClusterGroup());

					setRandomMapColor(newSpeciesNoBlanks);
					var marker = L.ExtraMarkers.icon({ icon: 'glyphicon-asterisk', markerColor: randomColor.get(newSpeciesNoBlanks)});


					if( el.total_catch_wt_kg>0 )
					{
						var bindHTML = '<table  class="display" cellspacing="0" cellpadding="5">'
						+'        <thead align="left">'
						+'            <tr class="metadataHeader">'
						+'                <th>Field&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'                <th>Value&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'            </tr>'
						+'        </thead>'
						+'        <tbody>';

						bindHTML +='<tr class="metadataEven"><td>Project&nbsp;&nbsp;&nbsp;</td><td>'+el.project_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Leg&nbsp;&nbsp;&nbsp;</td><td>'+el.leg+'</td></tr>'
						+'<tr class="metadataEven"><td>Date-Time (UTC)&nbsp;&nbsp;&nbsp;</td><td>'+el.date_dim$full_date+'</td></tr>'
						+'<tr class="metadataOdd"><td>Scientific Name&nbsp;&nbsp;&nbsp;</td><td>'+el.scientific_name+'</td></tr>'
						+'<tr class="metadataEven"><td>Common Name&nbsp;&nbsp;&nbsp;</td><td>'+el.common_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Vessel&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel+'</td></tr>'
						+'<tr class="metadataEven"><td>Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.site_dim$site_latitude_dd+'</td></tr>'
						+'<tr class="metadataEven"><td>Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.site_dim$site_longitude_dd+'</td></tr>'
						+'<tr class="metadataOdd"><td>Total Fish Caught per Site&nbsp;&nbsp;&nbsp;</td><td>'+el.total_catch_numbers+'</td></tr>'
						+'<tr class="metadataEven"><td>Total Catch Weight per Site (Kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.total_catch_wt_kg+'</td></tr>'
						+'<tr class="metadataOdd"><td>Area&nbsp;&nbsp;&nbsp;</td><td>'+el.site_dim$area_name+'</td></tr>'
						+'<tr class="metadataEven"><td>Site Number&nbsp;&nbsp;&nbsp;</td><td>'+el.site_dim$site_number+'</td></tr>'
						+'<tr class="metadataOdd"><td>Wave Height (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.wave_height_m+'</td></tr>'
						+'<tr class="metadataOdd"><td>Swell Direction (deg)&nbsp;&nbsp;&nbsp;</td><td>'+el.swell_direction_mag+'</td></tr>'
						+'<tr class="metadataEven"><td>Swell Height (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.swell_height_m+'</td></tr>'
						+'<tr class="metadataOdd"><td>Sea Surface Temperature (c)&nbsp;&nbsp;&nbsp;</td><td>'+Math.round(el.sea_surface_temp_c * 10)/10+'</td></tr>'
						+'<tr class="metadataEven"><td>Sounder Depth (CTD Drop) (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.ctd_sounder_depth_m+'</td></tr>'
						+'<tr class="metadataOdd"><td>CTD Measured Depth (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.ctd_on_bottom_measure_depth_dim$depth_meters+'</td></tr>'
						+'<tr class="metadataEven"><td>CTD Bottom Temperature (c)&nbsp;&nbsp;&nbsp;</td><td>'+el.ctd_on_bottom_temp_c+'</td></tr>'
						+'<tr class="metadataOdd"><td>CTD Salinity (psu)&nbsp;&nbsp;&nbsp;</td><td>'+el.ctd_on_bottom_salinity_psu+'</td></tr>'
						+'<tr class="metadataEven"><td>CTD Dissolved Oxygen - SBE43 (ml/l)&nbsp;&nbsp;&nbsp;</td><td>'+el.ctd_on_bottom_disolved_oxygen_sbe43_ml_per_l+'</td></tr>'
						+'<tr class="metadataOdd"><td>CTD Dissolved Oxygen - Aanderaa (ml/l)&nbsp;&nbsp;&nbsp;</td><td>'+el.ctd_on_bottom_disolved_oxygen_aanderaa_ml_per_l+'</td></tr>'
						;





						bindHTML +='</tbody></table>';

                        if(el.site_dim$site_latitude_dd!=null && el.site_dim$site_longitude_dd!=null)
						    layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).get(newSpeciesNoBlanks).addLayer(L.marker(L.latLng(el.site_dim$site_latitude_dd,el.site_dim$site_longitude_dd), { title: el.scientific_name , icon: marker}).bindPopup(bindHTML));
					}

				}; //end for loop


			while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).has(newSpeciesNoBlanks))
						map.addLayer(layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).get( newSpeciesNoBlanks ));

			}




			}); //end $http.get


		} // end dataSourceExistsBySpecies else condition
    }


    /**
     * Get trawl catch species data from DB and plot points based on input parameters
     */
    function getPlotTrawlCatch(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/trawl.catch_fact/selection.csv?variables=date_yyyymmdd,sampling_start_hhmmss,sampling_end_hhmmss,vessel,pass,leg,trawl_id,latitude_dd,longitude_dd,station_code,scientific_name,subsample_wt_kg,subsample_count,total_catch_wt_kg,total_catch_numbers,taxonomy_observation_detail_dim$measurement_procurement,partition,performance,depth_m,cpue_kg_per_ha_der,target_station_design_dim$date_stn_invalid_for_trawl_whid,statistical_partition_dim$statistical_partition_type,field_identified_taxonomy_dim$scientific_name,common_name,project';

		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.TRAWL.CATCH.key, self.checkedLayers) >= 0)
			showSpecies = true;

		var existingTrawlCatchData;
		var newSpecies = [];

		for(var i=0;i<j_species_codes.length;i++)
		{
			existingTrawlCatchData = showHideMarkers(FANCYTREE_ITEMS.TRAWL.CATCH.key,j_species_codes[i],showSpecies);

			if (!existingTrawlCatchData)
				newSpecies.push(j_species_codes[i]);
		}

		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{
			$http.get(get_stmt,{timeout: trawlCatchCanceler.promise, params: {scientific_name:newSpecies,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{

				var jsonArray = CSV2JSON(csv);
				csv = null;

				var data = JSON.parse( jsonArray );

				if(data[data.length-1].scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.TRAWL.CATCH.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.TRAWL.CATCH.key, new Dict() );


				var el;


				while (el = data.shift()) {

					var newSpeciesNoBlanks = (el.scientific_name).replace(/\s+/g, '');


					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).has( newSpeciesNoBlanks ) )
							layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).set(newSpeciesNoBlanks , L.markerClusterGroup());


					setRandomMapColor(el.scientific_name);
					  var marker = L.ExtraMarkers.icon({ icon: 'glyphicon-asterisk', markerColor: randomColor.get(el.scientific_name)});


					if( el.total_catch_wt_kg>0 )
					{


						var bindHTML = '<table  class="display" cellspacing="0" cellpadding="5">'
						+'        <thead align="left">'
						+'            <tr class="metadataHeader">'
						+'                <th>Field&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'                <th>Value&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'            </tr>'
						+'        </thead>'
						+'        <tbody>';


						bindHTML +='<tr class="metadataEven"><td>Date-Time (YYYYmmdd)&nbsp;&nbsp;&nbsp;</td><td>'+el.date_yyyymmdd+'</td></tr>'
						+'<tr class="metadataOdd"><td>Sampling Start Time (HHMMSS)&nbsp;&nbsp;&nbsp;</td><td>'+el.sampling_start_hhmmss+'</td></tr>'
						+'<tr class="metadataEven"><td>Sampling End Time (HHMMSS)&nbsp;&nbsp;&nbsp;</td><td>'+el.sampling_end_hhmmss+'</td></tr>'
						+'<tr class="metadataOdd"><td>Vessel&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel+'</td></tr>'
						+'<tr class="metadataEven"><td>Pass&nbsp;&nbsp;&nbsp;</td><td>'+el.pass+'</td></tr>'
						+'<tr class="metadataOdd"><td>Leg&nbsp;&nbsp;&nbsp;</td><td>'+el.leg+'</td></tr>'
						+'<tr class="metadataEven"><td>Haul ID&nbsp;&nbsp;&nbsp;</td><td>'+el.trawl_id+'</td></tr>'
						+'<tr class="metadataOdd"><td>Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.latitude_dd+'</td></tr>'
						+'<tr class="metadataEven"><td>Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.longitude_dd+'</td></tr>'
						+'<tr class="metadataOdd"><td>Station Code&nbsp;&nbsp;&nbsp;</td><td>'+el.station_code+'</td></tr>'
						+'<tr class="metadataEven"><td>Field Scientific Name&nbsp;&nbsp;&nbsp;</td><td>'+el.scientific_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Best Available Scientific Name&nbsp;&nbsp;&nbsp;</td><td>'+el.scientific_name+'</td></tr>'
						+'<tr class="metadataEven"><td>Best Available Common Name&nbsp;&nbsp;&nbsp;</td><td>'+el.common_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Subsample Weight (kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.subsample_wt_kg+'</td></tr>'
						+'<tr class="metadataEven"><td>Subsample Count&nbsp;&nbsp;&nbsp;</td><td>'+el.subsample_count+'</td></tr>'
						+'<tr class="metadataOdd"><td>Total Weight (kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.total_catch_wt_kg+'</td></tr>'
						+'<tr class="metadataEven"><td>Total Count&nbsp;&nbsp;&nbsp;</td><td>'+el.total_catch_numbers+'</td></tr>'
						+'<tr class="metadataOdd"><td>Weight Method&nbsp;&nbsp;&nbsp;</td><td>'+el.taxonomy_observation_detail_dim$measurement_procurement+'</td></tr>'
						+'<tr class="metadataEven"><td>Statistical Partition Value&nbsp;&nbsp;&nbsp;</td><td>'+el.partition+'</td></tr>'
						+'<tr class="metadataOdd"><td>Performance&nbsp;&nbsp;&nbsp;</td><td>'+el.performance+'</td></tr>'
						+'<tr class="metadataEven"><td>Seafloor Depth (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.depth_m+'</td></tr>'
						+'<tr class="metadataOdd"><td>CPUE Kg/Ha Derived&nbsp;&nbsp;&nbsp;</td><td>'+el.cpue_kg_per_ha_der+'</td></tr>'
						+'<tr class="metadataEven"><td>Project Name&nbsp;&nbsp;&nbsp;</td><td>'+el.project+'</td></tr>'
						+'<tr class="metadataOdd"><td>Date Station Invalid&nbsp;&nbsp;&nbsp;</td><td>'+el.target_station_design_dim$date_stn_invalid_for_trawl_whid+'</td></tr>'
						;

						bindHTML +='</tbody></table>';


						layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).get(newSpeciesNoBlanks).addLayer(L.marker(L.latLng(el.latitude_dd,el.longitude_dd), { title: el.scientific_name , icon: marker}).bindPopup(bindHTML));


					}

				}; //end for loop







			while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).has(newSpeciesNoBlanks))
						map.addLayer(layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).get( newSpeciesNoBlanks ));
			}


			}); //end $http.get
		} // end dataSourceExistsBySpecies else condition
    }








    /**
     * Get species data from DB and plot points based on input parameters
     */
    function getPlotTrawlSpecimens(j_species_codes,j_cycleStartDate,j_cycleEndDate) {


		var individualOrganismsTableData = [];

		var get_stmt = api_base_uri+'/api/v1/source/trawl.individual_fact/selection.csv?variables=date_yyyymmdd,sampling_start_hhmmss,sampling_end_hhmmss,vessel,pass,leg,trawl_id,field_identified_taxonomy_dim$scientific_name,scientific_name,common_name,latitude_dd,longitude_dd,station_code,sex_dim$sex,length_cm,age_years,weight_kg,depth_m,project';

		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, self.checkedLayers) >= 0)
			showSpecies = true;

		var existingSpeciesData = false;
		var newSpecies = [];






		for(var i=0;i<j_species_codes.length;i++)
		{
			existingSpeciesData = showHideMarkers(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key,j_species_codes[i],showSpecies);

			if (!existingSpeciesData)
				newSpecies.push(j_species_codes[i]);
		}



		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{

			$http.get(get_stmt,{timeout: trawlSpecimensCanceler.promise, params: {scientific_name:newSpecies,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{

				var jsonArray = CSV2JSON(csv);
				csv = null;

				var data = JSON.parse( jsonArray );

				if(data[data.length-1].scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, new Dict() );


				var el;
				var i=0;

				while (el = data.shift()) {

					var newSpeciesNoBlanks = (el.scientific_name).replace(/\s+/g, '');


					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).has( newSpeciesNoBlanks ) )
						layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).set(newSpeciesNoBlanks , L.markerClusterGroup());


					setRandomMapColor(el.scientific_name);
					var marker = L.ExtraMarkers.icon({ icon: 'glyphicon-asterisk', markerColor: randomColor.get(el.scientific_name)});


						var bindHTML = '<table  class="display" cellspacing="0" cellpadding="5">'
						+'        <thead align="left">'
						+'            <tr class="metadataHeader">'
						+'                <th>Field&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'                <th>Value&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>'
						+'            </tr>'
						+'        </thead>'
						+'        <tbody>';


						bindHTML +='<tr class="metadataEven"><td>Date (YYYYMMDD)&nbsp;&nbsp;&nbsp;</td><td>'+el.date_yyyymmdd+'</td></tr>'
						+'<tr class="metadataOdd"><td>Sampling Start Time (HHMMSS)&nbsp;&nbsp;&nbsp;</td><td>'+el.sampling_start_hhmmss+'</td></tr>'
						+'<tr class="metadataEven"><td>Sampling End Time (HHMMSS)&nbsp;&nbsp;&nbsp;</td><td>'+el.sampling_end_hhmmss+'</td></tr>'
						+'<tr class="metadataOdd"><td>Vessel&nbsp;&nbsp;&nbsp;</td><td>'+el.vessel+'</td></tr>'
						+'<tr class="metadataEven"><td>Pass&nbsp;&nbsp;&nbsp;</td><td>'+el.pass+'</td></tr>'
						+'<tr class="metadataOdd"><td>Leg&nbsp;&nbsp;&nbsp;</td><td>'+el.leg+'</td></tr>'
						+'<tr class="metadataEven"><td>Haul ID&nbsp;&nbsp;&nbsp;</td><td>'+el.trawl_id+'</td></tr>'
						+'<tr class="metadataEven"><td>Field Scientific Name&nbsp;&nbsp;&nbsp;</td><td>'+el.field_identified_taxonomy_dim$scientific_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Best Available Scientific Name&nbsp;&nbsp;&nbsp;</td><td>'+el.scientific_name+'</td></tr>'
						+'<tr class="metadataEven"><td>Best Available Common Name&nbsp;&nbsp;&nbsp;</td><td>'+el.common_name+'</td></tr>'
						+'<tr class="metadataOdd"><td>Latitude&nbsp;&nbsp;&nbsp;</td><td>'+el.latitude_dd+'</td></tr>'
						+'<tr class="metadataEven"><td>Longitude&nbsp;&nbsp;&nbsp;</td><td>'+el.longitude_dd+'</td></tr>'
						+'<tr class="metadataOdd"><td>Station Code&nbsp;&nbsp;&nbsp;</td><td>'+el.station_code+'</td></tr>'
						+'<tr class="metadataOdd"><td>Sex&nbsp;&nbsp;&nbsp;</td><td>'+el.sex_dim$sex+'</td></tr>'
						+'<tr class="metadataEven"><td>Length (cm)&nbsp;&nbsp;&nbsp;</td><td>'+el.length_cm+'</td></tr>'
						+'<tr class="metadataOdd"><td>Age&nbsp;&nbsp;&nbsp;</td><td>'+el.age_years+'</td></tr>'
						+'<tr class="metadataEven"><td>Weight (kg)&nbsp;&nbsp;&nbsp;</td><td>'+el.weight_kg+'</td></tr>'
						+'<tr class="metadataOdd"><td>Depth (m)&nbsp;&nbsp;&nbsp;</td><td>'+el.depth_m+'</td></tr>'

						;

						bindHTML +='</tbody></table>';




					layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).get(newSpeciesNoBlanks).addLayer(L.marker(L.latLng(el.latitude_dd,el.longitude_dd), { title: el.scientific_name , icon: marker}).bindPopup(bindHTML));


				}; //end for loop




			while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).has(newSpeciesNoBlanks))
						map.addLayer(layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).get( newSpeciesNoBlanks ));
			}


			}); //end $http.get
		} // end dataSourceExistsBySpecies else condition



    }




   /**
     * Takes a key (scientific name, vessel) input and sets a random Cesium map
	 * color for that ID. The first 10 colors are pre-selected to be bright.
     */
    function setRandomMapColor(key) {
		if (randomColor.get(key) == null)
		{
			if (leafletMarkerColorCounter==14)
				leafletMarkerColorCounter = 0;

			randomColor.set(key,leafletMarkerColorArray[leafletMarkerColorCounter] );
			leafletMarkerColorCounter++;
		}
	}



/*********************************************************************************************************************************************
	API calls to retrieve CSV file
**********************************************************************************************************************************************/

      function getConfCSV() {

			var get_stmt = api_base_uri+'/api/v1/source/observer.catch_observer_fact_conf/selection.csv?variables=discarded_catch_estimate_kg';
            var get_config = {responseType: 'blob'};//preserve raw response - see https://docs.angularjs.org/api/ng/service/$http#get

			$http.get(get_stmt, get_config).success(function(csv)
			{
				    var blob = new Blob([csv], {type: 'text/csv'});
					var filename =  'Conf.csv';
					saveCSV(blob,filename);
			});
	}
      function getHookLineCatchCSV(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

			var get_stmt = api_base_uri+'/api/v1/source/hooknline.catch_hooknline_view/selection.csv?variables=project_name,leg,date_dim$year,date_dim$full_date,scientific_name,common_name,vessel,site_dim$site_latitude_dd,site_dim$site_longitude_dd,total_catch_numbers,total_catch_wt_kg,site_dim$area_name,site_dim$site_number,wave_height_m,swell_direction_mag,swell_height_m,sea_surface_temp_c,ctd_sounder_depth_m,ctd_on_bottom_measure_depth_dim$depth_meters,ctd_on_bottom_temp_c,ctd_on_bottom_salinity_psu,ctd_on_bottom_disolved_oxygen_sbe43_ml_per_l,ctd_on_bottom_disolved_oxygen_aanderaa_ml_per_l';

			$http.get(get_stmt,{ params: {scientific_name:j_species_codes,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}, responseType: 'blob'}).success(function(csv)
			{
				    var blob = new Blob([csv], {type: 'text/csv'});
					var filename =  'HookLineCatch.csv';
					saveCSV(blob,filename);
			});
	}



    function getHookLineSpecimensCSV(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

			var get_stmt = api_base_uri+'/api/v1/source/hooknline.individual_hooknline_view/selection.csv?variables=project,leg,date_dim$year,date_dim$full_date,drop_time_dim$hh24miss,scientific_name,common_name,vessel,site_dim$area_name,site_dim$site_number,drop_latitude_dim$latitude_in_degrees,drop_longitude_dim$longitude_in_degrees,drop_sounder_depth_dim$depth_meters,hook_dim$hook_number,hook_dim$hook_result,sex_dim$sex,length_cm,age_years,weight_kg,otolith_number,fin_clip_number,tow,project_cycle';

			$http.get(get_stmt,{ params: {scientific_name:j_species_codes,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}, responseType: 'blob'}).success(function(csv)
			{
				    var blob = new Blob([csv], {type: 'text/csv'});
					var filename =  'HookLineSpecimens.csv';
					saveCSV(blob,filename);
			});
	}

    function getTrawlHaulCharsCSV(j_cycleStartDate,j_cycleEndDate) {

			var get_stmt = api_base_uri+'/api/v1/source/trawl.operation_haul_fact/selection.csv?variables=date_yyyymmdd,date_dim$year,sampling_start_hhmmss,sampling_end_hhmmss,project,vessel,pass,leg,trawl_id,performance,latitude_dd,longitude_dd,vessel_start_latitude_dd,vessel_start_longitude_dd,vessel_end_latitude_dd,vessel_end_longitude_dd,gear_start_latitude_dd,gear_start_longitude_dd,gear_end_latitude_dd,gear_end_longitude_dd,area_swept_ha_der,net_height_m_der,net_width_m_der,door_width_m_der,temperature_at_gear_c_der,temperature_at_surface_c_der,depth_hi_prec_m,turbidity_ntu_der,salinity_at_gear_psu_der,o2_at_gear_ml_per_l_der,vertebrate_weight_kg,invertebrate_weight_kg,nonspecific_organics_weight_kg,fluorescence_at_surface_mg_per_m3_der,target_station_design_dim$stn_invalid_for_trawl_date_whid';

			$http.get(get_stmt,{ params: {filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{
				    var blob = new Blob([csv], {type: 'text/csv'});
					var filename =  'TrawlHaulChars.csv';
					saveCSV(blob,filename);
			});
	}



    function getGEMMCSV(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

			var get_stmt = api_base_uri+'/api/v1/source/observer.gemm_fact/selection.csv';
            var get_config = {responseType: 'blob'};//preserve raw response - see https://docs.angularjs.org/api/ng/service/$http#get

			$http.get(get_stmt, get_config).success(function(csv)
			{
				   	var blob = new Blob([csv], {type: 'text/csv'});
					var filename =  'GEMM.csv';
					saveCSV(blob,filename);
			});
	}

    function getCatchExpansionsCSV(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/observer.catch_observer_view/selection.csv';
		var get_config = {responseType: 'blob'};//preserve raw response - see https://docs.angularjs.org/api/ng/service/$http#get

		$http.get(get_stmt, get_config).success(function(csv)
		{
				var blob = new Blob([csv], {type: 'text/csv'});
				var filename =  'Catch_Expansion.csv';
				saveCSV(blob,filename);
		});
}

    function getTrawlSpecimensCSV(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

			var get_stmt = api_base_uri+'/api/v1/source/trawl.individual_fact/selection.csv?variables=date_dim$year,date_yyyymmdd,sampling_start_hhmmss,sampling_end_hhmmss,vessel,pass,leg,trawl_id,field_identified_taxonomy_dim$scientific_name,scientific_name,common_name,latitude_dd,longitude_dd,station_code,sex_dim$sex,length_cm,age_years,weight_kg,depth_m,project,target_station_design_dim$stn_invalid_for_trawl_date_whid';

			$http.get(get_stmt,{ params: {scientific_name:j_species_codes,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}, responseType: 'blob'}).success(function(csv)
			{
				   	var blob = new Blob([csv], {type: 'text/csv'});
					var filename =  'TrawlSpecimens.csv';
					saveCSV(blob,filename);
			});
	}


    function getTrawlCatchCSV(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/trawl.catch_fact/selection.csv?variables=date_dim$year,date_yyyymmdd,sampling_start_hhmmss,sampling_end_hhmmss,vessel,pass,leg,trawl_id,latitude_dd,longitude_dd,station_code,scientific_name,subsample_wt_kg,subsample_count,total_catch_wt_kg,total_catch_numbers,taxonomy_observation_detail_dim$measurement_procurement,partition,performance,depth_m,cpue_kg_per_ha_der,target_station_design_dim$date_stn_invalid_for_trawl_whid,statistical_partition_dim$statistical_partition_type,field_identified_taxonomy_dim$scientific_name,common_name,project,target_station_design_dim$stn_invalid_for_trawl_date_whid';
			$http.get(get_stmt,{ params: {scientific_name:j_species_codes,filters:'date_yyyymmdd>='+j_cycleStartDate+',date_yyyymmdd<='+j_cycleEndDate}, responseType: 'blob'}).success(function(csv)
			{
				var blob = new Blob([csv], {type: 'text/csv'});
				var filename =  'TrawlCatch.csv';
				saveCSV(blob,filename);

			});
	}


	 function getObserverCatchCSV(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/observer.catch_observer_view/selection.csv?variables=taxonomy_dim$scientific_name,taxonomy_dim$common_name,season_year,report_category,catch_updated_date,discard_weight_est_lbs,discard_count_est';

		var start_season_year = j_cycleStartDate.substring(0, 4);
		var end_season_year = j_cycleEndDate.substring(0, 4);

			$http.get(get_stmt,{ params: {taxonomy_dim$scientific_name:j_species_codes,filters:'season_year>='+start_season_year+',season_year<='+end_season_year}, responseType: 'blob'}).success(function(csv)
			{
				   	var blob = new Blob([csv], {type: 'text/csv'});
					var filename =  'ObserverCatchExpansions.csv';
					saveCSV(blob,filename);
			});
	}

	function saveCSV(blob, filename) {
			if(window.navigator.msSaveOrOpenBlob) {
				window.navigator.msSaveBlob(blob, filename);
			}
			else{
				var elem = window.document.createElement('a');
				elem.href = window.URL.createObjectURL(blob);
				elem.download = filename;
				document.body.appendChild(elem);
				elem.click();
				document.body.removeChild(elem);
			}
	}

/*********************************************************************************************************************************************
	Time filter initialization / handlers to control time filter width based on window size
**********************************************************************************************************************************************/


$.event.special.widthChanged = {


        remove: function() {
            $(this).children('iframe.width-changed').remove();
        },
        add: function () {

            var elm = $(this);
            var iframe = elm.children('iframe.width-changed');

            if (!iframe.length) {

                iframe = $('<iframe/>').addClass('width-changed').prependTo(this);
            }

           var oldWidth = elm.width();


            function elmResized() {
                var width = elm.width();
                if (oldWidth != width) {
                    elm.trigger('widthChanged', [width, oldWidth]);
                    oldWidth = width;
                }
            }

            var timer = 0;

            var ielm = iframe[0];

            (ielm.contentWindow || ielm).onresize = function() {
                clearTimeout(timer);
                timer = setTimeout(elmResized, 20);
            };

        }
    }


	var timeplayerMargin = 45;

	var margin2 = {top: 0, right: 15, bottom: 20, left: 10},
    width = document.getElementById("paneWest").clientWidth-timeplayerMargin,// - margin2.left - margin2.right,
    height2 = 70 - margin2.top - margin2.bottom;



	var x2 = d3.time.scale()
		.domain([new Date('01/01/1975'),
     new Date('01/01/2020')
	]).range([0, width]),
		y = d3.scale.linear().range([height2, 0]),
		y2 = d3.scale.linear().range([height2, 0]);

	var  xAxis2 = d3.svg.axis().scale(x2).orient("bottom"),
		yAxis = d3.svg.axis().scale(y).orient("left");

	var brush = d3.svg.brush()
		.x(x2)
		.on("brushend", brushed);

	var extent =  brush.extent();

	var area2 = d3.svg.area()
		.interpolate("monotone")
		.x(function(d) { return x2(d.capture_date); })
		.y0(height2)
		.y1(function(d) { return y2(0); });//d.catches); });

	var svg = d3.select("timeplayer").attr("class", "chart").append("svg")
		.attr("width", width + margin2.left + margin2.right)
		.attr("height", height2 + margin2.top + margin2.bottom);

	svg.append("defs").append("clipPath")
		.attr("id", "clip")
	  .append("rect")
		.attr("width", width)
		.attr("height", height2);




	var focus = svg.append("g")
		.attr("class", "focus")
		.attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");

	var context = svg.append("g")
		.attr("class", "context")
		.attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");






$('#paneCenter').on('widthChanged',function(){

	var margin2 = {top: 0, right: 15, bottom: 20, left: 10},
    width =  document.getElementById("paneWest").clientWidth-timeplayerMargin,// - margin2.left - margin2.right,
	height2 = 70 - margin2.top - margin2.bottom;

	//remember the users start / end dates (extents)
	var extent =  brush.extent();

	svg.remove();

	x2 = d3.time.scale().domain([
    new Date('01/01/2015'),
     new Date('01/01/2026')
	]).range([0, width]),
		y = d3.scale.linear().range([height2, 0]),
		y2 = d3.scale.linear().range([height2, 0]);

	 xAxis2 = d3.svg.axis().scale(x2).orient("bottom"),
	 yAxis = d3.svg.axis().scale(y).orient("left");

	 brush = d3.svg.brush()
		.x(x2)
		.on("brushend", brushed);


	 area2 = d3.svg.area()
		.interpolate("monotone")
		.x(function(d) { return x2(d.capture_date); })
		.y0(height2)
		.y1(function(d) { return y2(1); });//d.catches); });

	 svg = d3.select("timeplayer").attr("class", "chart").append("svg")
		.attr("width", width + margin2.left + margin2.right)
		.attr("height", height2 + margin2.top + margin2.bottom);

	svg.append("defs").append("clipPath")
		.attr("id", "clip")
	  .append("rect")
		.attr("width", width)
		.attr("height", height2);


	 focus = svg.append("g")
		.attr("class", "focus")
		.attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");

	 context = svg.append("g")
		.attr("class", "context")
		.attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");


		var data = timefilterData;

		x2.domain(d3.extent(data.map(function(d) { return d; })));
		y2.domain([0, d3.max(data.map(function(d) { return 0; }))]);//return d.catches; }))]);



		  context.append("g")
			  .attr("class", "x axis")
			  .attr("transform", "translate(0," + height2 + ")")
			  .call(xAxis2);

		  context.append("g")
			  .attr("class", "x brush")
			.call(brush)
			.selectAll("rect")
			  .attr("y", -6)
			  .attr("height", height2 + 7);


		//set the user's start and end dates
		brush.extent([extent[0],extent[1]]);
		context.select('.brush').call(brush);

        $scope.$apply(function () {
            $scope.showTimeplayer = true;
        });

        //when window size changes, redraw the map
        map.invalidateSize();


});


/*********************************************************************************************************************************************
	Function to be called when time filter is updated
**********************************************************************************************************************************************/
	function brushed() {


		//clear all layers on the map
		map.eachLayer(function (layer) {

			if(layer.options.title!=undefined)
				map.removeLayer(layer);

		});


		layerToPrimitiveDict.clear();

		var startMonth = brush.extent()[0].getMonth()+1;
		var startDay = brush.extent()[0].getDate();

		var endMonth = brush.extent()[1].getMonth()+1;
		var endDay = brush.extent()[1].getDate();

		if (startMonth<10)
			startMonth = '0'+startMonth;


		if (startDay<10)
			startDay = '0'+startDay;

		if (endMonth<10)
			endMonth = '0'+endMonth;


		if (endDay<10)
			endDay = '0'+endDay;


		var startDateyyyymmdd = brush.extent()[0].getFullYear()+''+startMonth+''+startDay;
		var endDateyyyymmdd = brush.extent()[1].getFullYear()+''+endMonth+''+endDay;

		var startDate = (brush.extent()[0].getMonth()+1)+'/'+brush.extent()[0].getDate()+'/'+brush.extent()[0].getFullYear();
		var endDate = (brush.extent()[1].getMonth()+1)+'/'+brush.extent()[1].getDate()+'/'+brush.extent()[1].getFullYear();


		self.cycleStartDate =  brush.extent()[0];
		self.cycleEndDate =  brush.extent()[1];


        $scope.$apply(function () {
            self.startDate = self.cycleStartDate;
            self.endDate = self.cycleEndDate;
        });

		var j_species_codes = [];

		if (self.selectedSpecies!=null && self.selectedSpecies!='')
		 for (var i = 0; i < self.selectedSpecies.length; i++)
				j_species_codes.push(self.selectedSpecies[i].scientific_name);


		var list = self.checkedLayers;

		if ( $.inArray(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key, list)>=0 )
			getPlotTrawlHaulChars(startDateyyyymmdd,endDateyyyymmdd);

		if ( $.inArray(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, list)>=0 )
			getPlotTrawlSpecimens(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);

		if ( $.inArray(FANCYTREE_ITEMS.TRAWL.CATCH.key, list)>=0 )
			getPlotTrawlCatch(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);


		if ($.inArray(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, list) >= 0)
			getPlotHookLineSpecimens(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);

		if ($.inArray(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, list) >= 0)
			getPlotHookLineCatch(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);

		}


	//populate years, for the time filtere
	var timefilter_start_year = 1975 //start the time player from year 1975
	var timefilter_end_year = new Date().getFullYear()
	//if the current year is an odd year, it won't be displayed in the time filter
	//this makes sure that the last point in the time filter is an even year
	if( new Date('01/01/'+timefilter_end_year).getFullYear()%2 )
	{
		timefilter_end_year++
	}
	//Only 2x items are needed to populate the timeplayer
	var timefilter_data = [new Date('01/01/'+timefilter_start_year),new Date('01/01/'+timefilter_end_year)]
	x2.domain(d3.extent(timefilter_data.map(function(d) { return d; })));
	y2.domain([0, d3.max(timefilter_data.map(function(d) { return 0; }))]);//return d.catches; }))]);


	/*  context.append("path")
		  .datum(data)
		  .attr("class", "area")
		  .attr("d", area2);*/
	  context.append("g")
		  .attr("class", "x axis")
		  .attr("transform", "translate(0," + height2 + ")")
		  .call(xAxis2);

	  context.append("g")
		  .attr("class", "x brush")
		.call(brush)
		.selectAll("rect")
		  .attr("y", -6)
		  .attr("height", height2 + 7);


		//needed for $('#paneCenter').on('widthChanged',function()
		//as frame size changes, time filter is supposed to change sizee
	   timefilterData = timefilter_data;


		//Mak: resolve is used when canceling a service being called
		//don't remember why I had this in here but will leave it in here for now
		//commented out.
	   //timeplayerDefer.resolve(timefilter_data);


	$scope.updateTimeplayer = function() {

        if (self.startDate >= new Date('01/01/'+timefilter_start_year)
               && self.endDate <= new Date('12/31/'+timefilter_end_year) )
        {
            brush.extent([self.startDate, self.endDate]);
            brush(d3.select(".brush").transition());
            brush.event(d3.select(".brush").transition().delay(1000));

        }

	};

	$scope.updateOpacity = function(layer){
	    alert(layer);
    }



/*********************************************************************************************************************************************
	Map size initialization
**********************************************************************************************************************************************/
	if (self.mapHeight==null)
	{
			self.mapHeight = screen.height;//jQuery('.tabs-container').height();
			//jQuery('.tabs #tab1').height( self.mapHeight*0.632 );
			jQuery('.tabs #tab1').height( screen.height*0.68 );
			jQuery('.tabs #tab1' ).show().siblings().hide();
	}


/*********************************************************************************************************************************************
	Auto-brush time filter to the default dates (today - 3 years) - (today)
**********************************************************************************************************************************************/

	//set the user's start and end dates
	//brush.extent([extent[0],extent[1]]);
	//	context.select('.brush').call(brush);
	brush.extent([self.cycleStartDate, self.cycleEndDate])

    self.startDate = self.cycleStartDate;
    self.endDate = self.cycleEndDate;

    // now draw the brush to match our extent
    // use transition to slow it down so we can see what is happening
    // remove transition so just d3.select(".brush") to just draw
    brush(d3.select(".brush").transition());

    // now fire the brushstart, brushmove, and brushend events
    // remove transition so just d3.select(".brush") to just draw
    brush.event(d3.select(".brush").transition().delay(1000))


}]) //end View1Ctrl
