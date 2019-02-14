'use strict';

angular.module('myApp.view1', ['ngRoute','ngMaterial','angular-loading-bar','ngSanitize'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/map3d', {
    templateUrl: 'view1/view1.html'
  }).when('/map', {
    templateUrl: 'view2/view2.html'
  });

}])


.controller('View1Ctrl', ['$scope','$http', '$timeout', '$mdSidenav', '$mdUtil', '$log','$q', '$mdDialog', '$mdMedia',function($scope,$http, $timeout, $mdSidenav, $mdUtil, $log, $q,  $mdDialog, $mdMedia) {


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
+'<h4>Project Name (as listed in the web application, actual variable name = operation_dim$project_name when querying directly via the API)</h4>'
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
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012&variables=date_dim$yyyymmdd,field_identified_taxonomy_dim$scientific_name" target="_blank">https:\/\/www.nwfsc.noaa.gov\/data\/api\/v1\/source\/trawl.catch_fact\/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012<br>&variables=date_dim$yyyymmdd,field_identified_taxonomy_dim$scientific_name</a><br><br>'
+'Click on it and you should get back a stream of json-formatted data in your web browser that shows the date and scientific name that looks like the following:<br><br>'
+'<table  class="display" cellspacing="0" width="60%">'
+'        <thead align="left">'
+'            <tr class="metadataHeader">'
+'                <th>Sample json output&nbsp;&nbsp;&nbsp;</th>'
+'            </tr>'
+'        </thead>'
+'        <tbody>'

+'<tr class="metadataEven"><td>[{"date_dim$yyyymmdd": "20121009", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_dim$yyyymmdd": "20100822", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_dim$yyyymmdd": "20100822", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_dim$yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_dim$yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_dim$yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_dim$yyyymmdd": "20100823", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"},<br> {"date_dim$yyyymmdd": "20100824", "field_identified_taxonomy_dim$scientific_name": "Eopsetta jordani"}, </td></tr>'


+'        </tbody>'
+' </table>	<br><br>'
+'If you\'d prefer a csv download of the data, change selection.json to selection.csv as follows:<br><br>'
+'<i>csv output</i><br>'
+'<a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.csv?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012&variables=date_dim$yyyymmdd,field_identified_taxonomy_dim$scientific_name" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.csv?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012><br>&variables=date_dim$yyyymmdd,field_identified_taxonomy_dim$scientific_name</a><br><br>'
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
+'<tr class="metadataEven"><td>Requested Variables</td><td>List of variables, comma separated, that you want to return, leave blank to return all variables (but this will incur a performance hit due to the large number of variables)</td><td>variables=date_dim$yyyymmdd,field_identified_taxonomy_dim$scientific_name</td></tr>'
+'<tr class="metadataOdd"><td>Complete URL</td><td>The full URL</td><td><a href="https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012&variables=date_dim$yyyymmdd,field_identified_taxonomy_dim$scientific_name" target="_blank">https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.catch_fact/selection.json?filters=field_identified_taxonomy_dim$scientific_name=Eopsetta%20jordani,date_dim$year>=2010,date_dim$year<=2012<br>&variables=date_dim$yyyymmdd,field_identified_taxonomy_dim$scientific_name</a></td></tr>'

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
+'<tr class="metadataEven"><td>Trawl Survey Haul Characteristics (includes environmental data)</td><td>trawl.operation_haul_fact&nbsp;&nbsp;</td><td><a href="https://www.nwfsc.noaa.gov/datta/api/v1/source/trawl.operation_haul_fact/variables" target="_blank">https://www.nwfsc.noaa.gov/datta/api/v1/source/trawl.operation_haul_fact/variables</a></td></tr>'
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
+'<h2>Web Browser Requirements</h2>'
+'The FRAM Data Warehouse uses the <a href="http://www.cesiumjs.org/" target="_blank">cesiumjs</a> 3D mapping software. CesiumJS in turn uses <a href="https://en.wikipedia.org/wiki/WebGL" target="_blank">WebGL</a> technology, allowing one to render video card-accelerated 3D graphics natively in a web browser, without requiring the use of any plugins. However not all web browsers support WebGL to the same level. You can check if your web browser supports WebGL at the link below:<br><br>'
+'<a href="http://caniuse.com/#feat=webgl" target="_blank">http://caniuse.com/#feat=webgl</a>'
+'<h2>Customer Survey</h2>'
+'We welcome your feedback. Please provide this via the following customer survey: <a href="http://www8.nos.noaa.gov/survey/index.aspx?Location=nwfsc" target="_blank">http://www8.nos.noaa.gov/survey/index.aspx?Location=nwfsc</a>'
+'<h2>Privacy Policy</h2>'
+'We take your privacy very seriously and we follow the standard NOAA privacy policy that is outlined here: <a href="http://www.noaa.gov/protecting-your-privacy" target="_blank">http://www.noaa.gov/protecting-your-privacy</a>'
+'<h2>External Link Endorsement</h2>'
+'The appearance of external links on this Web site does not constitute endorsement by the Department of Commerce/National Oceanic and Atmospheric Administration of external Web sites or the information, products or services contained therein. For other than authorized activities, the Department of Commerce/NOAA does not exercise any editorial control over the information you may find at these locations. These links are provided consistent with the stated purpose of this Department of Commerce/NOAA Web site.';


/*********************************************************************************************************************************************
	Meta data tool button events/binds
**********************************************************************************************************************************************/
	$( "#about" ).bind( "click", function( ev ) { 
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

	});

	$("#about").mousedown(function() {

		$(this).attr("src","images/i3.png");
	});

	$("#about").hover(function() {
		$(this).attr("src","images/i2.png");
		$(this).css("cursor", "pointer");
		$(this).css(
            "box-shadow", "0px 0px 2px 1px #AAEEFF"
        );
			}, function() {
		$(this).attr("src","images/i1.png");
		 $(this).css( "box-shadow", "none" );
	});


	$( "#contactUs" ).bind( "click", function( ev ) { 
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

	});

	$("#contactUs").mousedown(function() {

		$(this).attr("src","images/email3.png");
	});

	$("#contactUs").hover(function() {
		$(this).attr("src","images/email2.png");
		$(this).css("cursor", "pointer");
		$(this).css(
            "box-shadow", "0px 0px 2px 1px #AAEEFF"
        );
			}, function() {
		$(this).attr("src","images/email1.png");
		 $(this).css( "box-shadow", "none" );
	});

	$( "#api" ).bind( "click", function( ev ) { 
			$mdDialog.show(
			  $mdDialog.alert()
				.parent(angular.element(document.querySelector('#popupContainer')))
				.clickOutsideToClose(true)
		//		.title('API')
				.htmlContent(apiContent)
				.ariaLabel('API')
				.ok('Close')
				.targetEvent(ev)
			);

	});
	$("#api").mousedown(function() {

		$(this).attr("src","images/API3.png");
	});

	$("#api").hover(function() {
		$(this).attr("src","images/API2.png");
		$(this).css("cursor", "pointer");
		$(this).css(
            "box-shadow", "0px 0px 2px 1px #AAEEFF"
        );
			}, function() {
		$(this).attr("src","images/API1.png");
		 $(this).css( "box-shadow", "none" );
	});

	$( "#citation" ).bind( "click", function( ev ) { 
			$mdDialog.show(
			  $mdDialog.alert()
				.parent(angular.element(document.querySelector('#popupContainer')))
				.clickOutsideToClose(true)
			//	.title('Citation')
				.htmlContent(citationContent)
				.ariaLabel('Citation')
				.ok('Close')
				.targetEvent(ev)
			);

	});


	$("#citation").mousedown(function() {

		$(this).attr("src","images/chat3.png");

	});

	$("#citation").hover(function() {
		$(this).attr("src","images/chat2.png");
		$(this).css("cursor", "pointer");
		$(this).css(
            "box-shadow", "0px 0px 2px 1px #AAEEFF"
        );
			}, function() {
		$(this).attr("src","images/chat1.png");
		 $(this).css("box-shadow", "none");
	});


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
				lastDateUpdated = new Date(data.sources[i].updated);
				lastDateUpdated = (lastDateUpdated.getMonth() + 1) +'/'+ lastDateUpdated.getDate() +'/'+ lastDateUpdated.getFullYear()
					+' '+lastDateUpdated.getHours()+':'+lastDateUpdated.getMinutes() +':'+lastDateUpdated.getSeconds();

				if(i%2==0)
					metaData +='<tr class="metadataEven"><td>'+data.sources[i].project+' '+data.sources[i].name+'</td>';
				else
					metaData +='<tr class="metadataOdd"><td>'+data.sources[i].project+' '+data.sources[i].name+'</td>';
				metaData +='<td>'+data.sources[i].description+'</td>';
				metaData +='<td>'+data.sources[i].rows+'</td>';
				metaData +='<td>'+lastDateUpdated+'</td>';
				metaData +='<td>'+data.sources[i].years+'</td>';
				metaData +='<td>'+data.sources[i].contact.replace("<","").replace(">","")+'</td></tr>';

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
		'                <th>Layer&nbsp;&nbsp;&nbsp;</th>'+
		'                <th>Description&nbsp;&nbsp;&nbsp;</th>'+
		'                <th>Records&nbsp;</th>'+
		'                <th>Updated&nbsp;&nbsp;&nbsp;</th>'+
		'                <th>Years of Data</th>'+
			'                <th>Point of Contact</th>'+
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
	Different imagery models (such as ESRI World with label...)
**********************************************************************************************************************************************/

var imageryViewModels = [];

imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI World with Labels', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/imagery_labels.png'),
    tooltip: 'World Imagery provides one meter or better satellite and aerial imagery in many parts of the world and lower resolution satellite imagery worldwide.  The map includes NASA Blue Marble: Next Generation 500m resolution imagery at small scales (above 1:1,000,000), i-cubed 15m eSAT imagery at medium-to-large scales (down to 1:70,000) for the world, and USGS 15m Landsat imagery for Antarctica. The map features 0.3m resolution imagery in the continental United States and 0.6m resolution imagery in parts of Western Europe from DigitalGlobe. In other parts of the world, 1 meter resolution imagery is available from GeoEye IKONOS,  i-cubed Nationwide Prime, Getmapping, AeroGRID, IGN Spain, and IGP Portugal.  Additionally, imagery at different resolutions has been contributed by the GIS User Community.\nhttp://www.esri.com', 
      creationFunction : function() {
         return [new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',
            enablePickFeatures: false}),
			new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer',
            enablePickFeatures: false})]
			
		;
     }
 }));


imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI World', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/esriWorldImagery.png'),
    tooltip: 'World Imagery provides one meter or better satellite and aerial imagery in many parts of the world and lower resolution satellite imagery worldwide.  The map includes NASA Blue Marble: Next Generation 500m resolution imagery at small scales (above 1:1,000,000), i-cubed 15m eSAT imagery at medium-to-large scales (down to 1:70,000) for the world, and USGS 15m Landsat imagery for Antarctica. The map features 0.3m resolution imagery in the continental United States and 0.6m resolution imagery in parts of Western Europe from DigitalGlobe. In other parts of the world, 1 meter resolution imagery is available from GeoEye IKONOS,  i-cubed Nationwide Prime, Getmapping, AeroGRID, IGN Spain, and IGP Portugal.  Additionally, imagery at different resolutions has been contributed by the GIS User Community.\nhttp://www.esri.com', 
      creationFunction : function() {
         return new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',
            enablePickFeatures: false});
     }
 }));


imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI World Street Map', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/esriWorldStreetMap.png'),
    tooltip: 'This map features highway-level data for the world and street-level data for North America, Europe, and other parts of the world.\nhttp://www.esri.com', 
      creationFunction : function() {
         return new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer',
            enablePickFeatures: false});
     }
 }));


imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI Topographic', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/topo_map_2.png'),
    tooltip: 'This topographic map is designed to be used as a basemap and a reference map. The map has been compiled by Esri and the ArcGIS user community from a variety of best available sources.\nhttp://www.esri.com', 
      creationFunction : function() {
         return new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer',
            enablePickFeatures: false});
     }
 }));

imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI National Geographic', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/esriNationalGeographic.png'),
    tooltip: 'This map features the National Geographic World Map, which is a cartographically rich and distinctive reference map of the world.\nhttp://www.esri.com', 
      creationFunction : function() {
         return new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer',
            enablePickFeatures: false});
     }
 }));

imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI Dark Gray', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/DGCanvasBase.png'),
    tooltip: 'This map is designed to focus attention on your thematic content by providing a neutral background with minimal colors, labels, and features.\nhttp://www.esri.com', 
      creationFunction : function() {
         return [new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer',
            enablePickFeatures: false}),
			new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer',
            enablePickFeatures: false})]
			
     }
 }));


imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI Light Gray', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/light_gray_canvas.png'),
    tooltip: 'This map is designed to focus attention on your thematic content by providing a neutral background with minimal colors, labels, and features.\nhttp://www.esri.com', 
      creationFunction : function() {
         return [new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer',
            enablePickFeatures: false}),
			new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer',
            enablePickFeatures: false})]
			
     }
 }));



imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI Oceans', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/tempoceans.png'),
    tooltip: 'This map is designed to be used as a basemap by marine GIS professionals and as a reference map by anyone interested in ocean data.\nhttp://www.esri.com', 
      creationFunction : function() {
         return [new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer',
            enablePickFeatures: false}),
			new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Reference/MapServer',
            enablePickFeatures: false})]
			
     }
 }));


imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI Terrain with Labels', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/terrain_labels.png'),
    tooltip: 'This map features shaded relief imagery, bathymetry and coastal water features that provide neutral background with political boundaries and placenames for reference purposes.\nhttp://www.esri.com', 
      creationFunction : function() {
         return [new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer',
            enablePickFeatures: false}),
			new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Reference_Overlay/MapServer',
            enablePickFeatures: false})]
			
     }
 }));


imageryViewModels.push(new Cesium.ProviderViewModel({
     name :  'ESRI USA Topo', 
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/usa_topo.png'),
    tooltip: 'This map features detailed USGS topographic maps for the United States at multiple scales.\nhttp://www.esri.com', 
      creationFunction : function() {
         return [new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places_Alternate/MapServer',
            enablePickFeatures: false}),
			new Cesium.ArcGisMapServerImageryProvider({
        url : 'https://services.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer',
            enablePickFeatures: false})]
			
     }
 }));


 imageryViewModels.push(new Cesium.ProviderViewModel({
     name : 'Open\u00adStreet\u00adMap',
     iconUrl : Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
     tooltip : 'OpenStreetMap (OSM) is a collaborative project to create a free editable \
map of the world.\nhttp://www.openstreetmap.org',
     creationFunction : function() {
         return new Cesium.OpenStreetMapImageryProvider({
             url : 'https://a.tile.openstreetmap.org/'
         });
     }
 }));


/*********************************************************************************************************************************************
	CesiumJS initialization
**********************************************************************************************************************************************/

    var viewer = new Cesium.Viewer('cesiumContainer', {
        timeline : false,
        navigationHelpButton: true,
        scene3DOnly: false,
        fullscreenButton: false,
        baseLayerPicker:false,
        homeButton:true	,
        infoBox:true,
        sceneModePicker:true,
        selectionIndicator: true,
        animation:false,
        geocoder:false,
		imageryProvider : false ,
        sceneMode : Cesium.SceneMode.SCENE3D
    });


	var baseLayerPicker = new Cesium.BaseLayerPicker('baseLayerPickerContainer', {globe:viewer.scene.globe, imageryProviderViewModels:imageryViewModels});

	 viewer.camera.flyTo({
        destination : Cesium.Cartesian3.fromDegrees(55.0000, 140.5, 4500000.0)
    });

    // Mouse over the globe to see the cartographic position
	var scene = viewer.scene;

	// This ensures that when the points are removed from the map
	// they do not get destroyed. This way we can show them again without an API call.
	scene.primitives.destroyPrimitives = false;


	//layers is used to add ArcGIS layers
	var layers = viewer.scene.imageryLayers;

	var helper = new Cesium.EventHelper();

	helper.add(viewer.homeButton.viewModel.command.afterExecute, zoomToWestCoast, this);

    /**
     * Zooms camera to the west coast
     */
    function zoomToWestCoast() {
		viewer.camera.flyTo({
			destination : Cesium.Cartesian3.fromDegrees(55.0000, 140.5, 4500000.0)
		});
    }

/*********************************************************************************************************************************************
	Map handlers (Map point click to Datatable integration)
**********************************************************************************************************************************************/

	//handler is used to detect user map click so we can select the 
	//corresponding datatable row
    var handler = new Cesium.ScreenSpaceEventHandler(scene.canvas);


	//Handle latitude/longitude display at the bottom right of the map
	$( "#paneCenter" ).bind( "mouseenter", function( event ) { 
		handler.setInputAction(function(movement) {
			var cartesian = viewer.camera.pickEllipsoid(movement.endPosition, scene.globe.ellipsoid);

			if (cartesian) {
				var cartographic = Cesium.Ellipsoid.WGS84.cartesianToCartographic(cartesian);

				var longitudeString = Cesium.Math.toDegrees(cartographic.longitude).toFixed(6);
				var latitudeString = Cesium.Math.toDegrees(cartographic.latitude).toFixed(6);

				$("#lat-long").html('Latitude: ' + latitudeString+ ' Longitude: ' + longitudeString );
			} 

		}, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

	});

	//remove the input action when mouse leaves the map pane
	$( "#paneCenter" ).bind( "mouseleave", function( event ) { 
		handler.removeInputAction( Cesium.ScreenSpaceEventType.MOUSE_MOVE);

	});
	
	//Handle point primitive click so that the corresponding datatable row is selected
	handler.setInputAction(function(click) {

		var drillPickedObject = scene.drillPick(click.position);

		var pickedObject;

		//go through all the points where the user clicked on the map
		//pick the first point that belongs to the currently shown datatable
		while ( pickedObject = drillPickedObject.shift() ) 
			if( pickedObject.id.layer == currentSelectedDatatable )
				break;

		  if (Cesium.defined(pickedObject) ) {

				var cartographic =  Cesium.Ellipsoid.WGS84.cartesianToCartographic(pickedObject.primitive.position);
				var index;

				//set pickingMapInput to true so that the datatable 
				//onSelect bind doesn't try to locate the map point
				pickingMapInput = true;

				//deselect all datatable rows
				trawlCatchDataTable.$('tr.selected').removeClass('selected');
				hookLineSpecimensDataTable.$('tr.selected').removeClass('selected');
				hookLineCatchDataTable.$('tr.selected').removeClass('selected');
				trawlHaulCharsDataTable.$('tr.selected').removeClass('selected');

				//get the index of the map point 
				if (pickedObject.id.scientificName)
					index = pickedObject.id.scientificName.replace(/\s+/g, '')+pickedObject.id.index;
				else
					index = pickedObject.id.index;
					
				//add selected class to the corresponding datatables
				switch(pickedObject.id.layer) {
					case FANCYTREE_ITEMS.TRAWL.SPECIMENS.key:
						trawlSpecimensDataTable.rows('#'+index).select();
						trawlSpecimensDataTable.row('#'+index).scrollTo();
						break;
					case FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key:
						hookLineSpecimensDataTable.rows('#'+index).select();
						hookLineSpecimensDataTable.row('#'+index).scrollTo();
						break;
					case FANCYTREE_ITEMS.HOOK_LINE.CATCH.key:
						hookLineCatchDataTable.rows('#'+index).select();
						hookLineCatchDataTable.row('#'+index).scrollTo();
						break;
					case FANCYTREE_ITEMS.TRAWL.CATCH.key:
						trawlCatchDataTable.rows('#'+index).select();
						trawlCatchDataTable.row('#'+index).scrollTo();
						break;
					case FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key:
						trawlHaulCharsDataTable.rows(index).select();
						trawlHaulCharsDataTable.row(index).scrollTo();
						break;
				}
				
				//set pickingMapInput to false so that the datatable binds work as expected
				pickingMapInput = false;

				viewer.entities.removeAll();
				var entityName;
				if(pickedObject.id.scientificName)
					entityName = pickedObject.id.scientificName+' '+pickedObject.id.index;
				else
					entityName = pickedObject.id.vessel;

				var entity = new Cesium.Entity({
								name: entityName,
								position : Cesium.Cartesian3.fromDegrees(Cesium.Math.toDegrees(cartographic.longitude), Cesium.Math.toDegrees(cartographic.latitude)),
								id : pickedObject.id.layer,

								scaleByDistance : new Cesium.NearFarScalar(1.5e2, 1.0, 1.5e7, 0.5),
								point : {
									pixelSize : 10,
									color : randomColor.get(pickedObject.id.scientificName)
								}
							});

				viewer.entities.add(entity);
				viewer.selectedEntity = entity;

				
		  }
				

	 }, Cesium.ScreenSpaceEventType.LEFT_CLICK );



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
	$scope.disableSpeciesFilter = true;
	var self = this;
	var j_cycleStartDate = '1/1/1900';
	var j_cycleEndDate = '1/1/3000';
	
	//this field is used to make sure when the user clicks on a map primitive point
	//it doesn't create a circular effect when selecting the datatable row
	//by calling the map point back
	var pickingMapInput = false;


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
	var layerToPrimitiveIndexDict = new Dict();
	var layerToPrimitiveDict = new Dict();

	//hashmaps to store datatable data
	var trawlSpecimensPointPrimitivesDict = new Dict();
	var trawlSpecimensDataTableDict = new Dict();
	var trawlHaulCharsDataTableArray = [];
	var trawlCatchDataTableDict = new Dict();
	var hookLineSpecimensDataTableDict = new Dict();
	var hookLineCatchDataTableDict = new Dict();
	var observerCatchDataTableDict = new Dict();
	var currentSelectedDatatable;

	//used to show/hide datatable buttons in the south pane
	$scope.extensionsBtnShow = false;
	$scope.trawlCatchBtnShow = false;
	$scope.trawlSpecimensBtnShow = false;
	$scope.trawlHaulCharsBtnShow = false;
	$scope.hookLineSpecimensBtnShow = false;
	$scope.hookLineCatchBtnShow = false;


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

	//Predefined top ten CesiumJS colors
	var topTenCesiumColorArray = [Cesium.Color.LIME,Cesium.Color.GOLD ,
		Cesium.Color.ORANGERED,Cesium.Color.SKYBLUE,Cesium.Color.GHOSTWHITE,Cesium.Color.MAGENTA,Cesium.Color.MEDIUMSPRINGGREEN ,
		Cesium.Color.LIGHTCYAN ,  Cesium.Color.CORAL,Cesium.Color.ROYALBLUE];
	var topTenCesiumColorCounter = 0;

	var datatableIds = ["#trawl_catch_table","#trawl_specimens_table","#trawl_haul_chars_table","#hook_line_specimens_table","#hook_line_catch_table","#observer_catch_table"];


	//showProgram, showDataType is used to toggle between fancy tree groups
	var currentFancyTree = '#layers';
	$scope.showProgram = function() {
		$scope.programBtnChecked = true;
		currentFancyTree = '#layers';
	};
	$scope.showDataType = function() {
		$scope.programBtnChecked = false;
		currentFancyTree = '#layers-content';
	};

	//ArcGIS layer variables
	var acousticsNASC2012Layer = null;
	var acousticsNASC2013Layer = null;
	var acousticsNASC2015Layer = null;
	var acousticsSonarDataLayer = null;
	var acousticsVesselTransectsLayer = null;
	var trawlSurveyStationGridLayer = null;
	var hookLineSamplingSitesLayer = null;
	var spatialReferencesBathymetricCountoursLayer = null;
	var spatialReferencesHabitat361MapLayer = null;
	var spatialReferencesHabitat40MapLayer = null;
	var spatialReferencesMarineProtectedAreasLayer = null;
	var spatialReferencesNMFSTrawlRCALayer = null;
	var spatialReferencesRegulatoryBoundariesLayer = null;
	var spatialReferencesRegulatoryBoundariesPFMCLandmarksLayer = null;
	var spatialReferencesRegulatoryBoundariesINPFCAreasLayer = null;

/*********************************************************************************************************************************************
	Setup datatable buttons and the button events
**********************************************************************************************************************************************/
	//function shows and adjusts a particular datatable and hides others
	//tableId corresponds to the HTML table ID, if blank, hide all tables
    function showDatatable(tableId) {

		for (var i = 0; i < datatableIds.length; i++) { 
			if(datatableIds[i]==tableId)
			{
				$(tableId).parents('div.dataTables_wrapper').first().show();
				$(tableId).dataTable().fnAdjustColumnSizing( false );
					
				switch(tableId) {	
					case "#trawl_specimens_table":
						currentSelectedDatatable = FANCYTREE_ITEMS.TRAWL.SPECIMENS.key;
						break;
					case "#hook_line_specimens_table":
						currentSelectedDatatable = FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key;
						break;
					case "#hook_line_catch_table":
						currentSelectedDatatable = FANCYTREE_ITEMS.HOOK_LINE.CATCH.key;
						break;
					case "#trawl_catch_table":
						currentSelectedDatatable = FANCYTREE_ITEMS.TRAWL.CATCH.key;
						break;
					case "#trawl_haul_chars_table":
						currentSelectedDatatable = FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key;
						break;
					case "#observer_catch_table":
						currentSelectedDatatable = FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key;
						break;
				}

			}
			else
				$(datatableIds[i]).parents('div.dataTables_wrapper').first().hide();

		}

	}

    $( "#radio" ).buttonset();

	//Catch datatable button
	$( "#radio2" ).click(function() {
		showDatatable("#trawl_catch_table");
		
	});

	//Haul Characteristics datatable button
	$( "#radio3" ).click(function() {
		showDatatable("#trawl_haul_chars_table");
	});


	//Individual Organisms datatable button
	$( "#radio4" ).click(function() {
		showDatatable("#trawl_specimens_table");
	});


	//Hook & Line Specimens datatable button
	$( "#radio5" ).click(function() {
		showDatatable("#hook_line_specimens_table");
	});


	//Hook & Line Specimens datatable button
	$( "#radio6" ).click(function() {
		showDatatable("#hook_line_catch_table");
	});

	//Observer catch datatable button
	$( "#radio7" ).click(function() {
		showDatatable("#observer_catch_table");
	});

	//manage tabs
	jQuery(document).ready(function() {
		// Standard
		jQuery('.tabs.standard .tab-links a').on('click', function(e)  {
			var currentAttrValue = jQuery(this).attr('href');

		if(currentAttrValue == '#tab1')
		{
					jQuery('.tabs ' + currentAttrValue).height( self.mapHeight*0.68 );
		}
		else
			{
			jQuery('.tabs ' + currentAttrValue).height( self.mapHeight*0.682 );
			}

			// Show/Hide Tabs
			jQuery('.tabs ' + currentAttrValue).show().siblings().hide();
		
			// Change/remove current tab to active
			jQuery(this).parent('li').addClass('active').siblings().removeClass('active');

			e.preventDefault();
		});


	});


/*********************************************************************************************************************************************
	FancyTree initialization / layer ordering
**********************************************************************************************************************************************/

	$("#layers").fancytree({
	  source: [
		  		{title: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.key, folder: true, expanded: true, children: [
		  {title: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.key, data:{layer:acousticsNASC2012Layer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.mapServices}, icon: false},
		  {title: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.key, data:{layer:acousticsNASC2013Layer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.mapServices}, icon: false},
		  {title: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.key, data:{layer:acousticsNASC2015Layer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.mapServices}, icon: false},
		  {title: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.key, data:{layer:acousticsSonarDataLayer,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.mapServices}, icon: false},
	      {title: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.VESSEL_TRANSECTS.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.VESSEL_TRANSECTS.key, data:{layer:acousticsVesselTransectsLayer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.VESSEL_TRANSECTS.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.VESSEL_TRANSECTS.mapServices}, icon: false}
		]},	

		{title: FANCYTREE_ITEMS.EFH.title, key: FANCYTREE_ITEMS.EFH.key, folder: true, expanded: true, children: [

			  {title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.key, folder: true, expanded: true, children: [
					 {title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.key, data:{layer:spatialReferencesHabitat361MapLayer  ,url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.mapServices}, icon: false},
				{title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.key, data:{layer:spatialReferencesHabitat40MapLayer  ,url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.mapServices}, icon: false}
				]}
		]},
			{title: FANCYTREE_ITEMS.HOOK_LINE.title, key: FANCYTREE_ITEMS.HOOK_LINE.key, folder: true, expanded: true, children: [
		  {title: FANCYTREE_ITEMS.HOOK_LINE.CATCH.title, key: FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, icon: false},
		  {title: FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.title, key: FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.key, data:{layer:hookLineSamplingSitesLayer  ,url:FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.url, mapServices:FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.mapServices}, icon: false},
		  {title: FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.title, key: FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, icon: false}
		]},	
		{title: FANCYTREE_ITEMS.OBSERVER.title, key: FANCYTREE_ITEMS.OBSERVER.key, folder: true, expanded: true, children: [
		  {title: FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.title, key: FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key, icon: false}
		]},	 
	
	  {title: FANCYTREE_ITEMS.TRAWL.title, key: FANCYTREE_ITEMS.TRAWL.key, folder: true, expanded: true, children: [
		{title: FANCYTREE_ITEMS.TRAWL.CATCH.title, key: FANCYTREE_ITEMS.TRAWL.CATCH.key, icon: false},
		{title: FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.title, key: FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key, icon: false},
		  {title: FANCYTREE_ITEMS.TRAWL.SPECIMENS.title , key: FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, icon: false},
		{title: FANCYTREE_ITEMS.TRAWL.STATION_GRID.title, key: FANCYTREE_ITEMS.TRAWL.STATION_GRID.key, data:{layer:trawlSurveyStationGridLayer  ,url:FANCYTREE_ITEMS.TRAWL.STATION_GRID.url, mapServices:FANCYTREE_ITEMS.TRAWL.STATION_GRID.mapServices}, icon: false}
		]},
		{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.key, folder: true, expanded: true, children: [
		  {title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.key, data:{layer:spatialReferencesBathymetricCountoursLayer  ,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.mapServices}, icon: false},
		{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.key, data:{layer:spatialReferencesMarineProtectedAreasLayer,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.mapServices}, icon: false},
		{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.key, data:{layer:spatialReferencesNMFSTrawlRCALayer,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.mapServices}, icon: false},

				{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.key, folder: true, expanded: true, children: [
				 {title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.key, data:{layer:spatialReferencesRegulatoryBoundariesPFMCLandmarksLayer,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.mapServices}, icon: false},
			{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.key, data:{layer:spatialReferencesRegulatoryBoundariesINPFCAreasLayer ,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.mapServices}, icon: false}
				]},	
		]}
	  ],
	  checkbox: true,
	  selectMode:3
	});

	$("#layers-content").fancytree({
	  source: [
		{title: FANCYTREE_ITEMS.CATCH.title, key: FANCYTREE_ITEMS.CATCH.key, folder: true, expanded: true, children: [
		  		  {title: FANCYTREE_ITEMS.CATCH.NASC_2012.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.key, data:{layer:acousticsNASC2012Layer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2012.mapServices}, icon: false},
		  {title: FANCYTREE_ITEMS.CATCH.NASC_2013.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.key, data:{layer:acousticsNASC2013Layer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2013.mapServices}, icon: false},
		  {title: FANCYTREE_ITEMS.CATCH.NASC_2015.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.key, data:{layer:acousticsNASC2015Layer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.NASC_2015.mapServices}, icon: false},

		  {title: FANCYTREE_ITEMS.HOOK_LINE.title+' (by Site)', key: FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, icon: false},
			{title: FANCYTREE_ITEMS.OBSERVER.title, key: FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key, icon: false},
			{title: FANCYTREE_ITEMS.TRAWL.title, key: FANCYTREE_ITEMS.TRAWL.CATCH.key, icon: false}
	    ]},
		
		{title: FANCYTREE_ITEMS.EFH.title, key: FANCYTREE_ITEMS.EFH.key, folder: true, expanded: true, children: [

			  {title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.key, folder: true, expanded: true, children: [
					 {title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.key, data:{layer:spatialReferencesHabitat361MapLayer  ,url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_3_6_1.mapServices}, icon: false},
				{title: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.title, key: FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.key, data:{layer:spatialReferencesHabitat40MapLayer  ,url:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.url, mapServices:FANCYTREE_ITEMS.EFH.HABITAT_MAP.OSU_ATSML_4_0.mapServices}, icon: false}
			]}
			]},

		{title: FANCYTREE_ITEMS.OPERATION_CHARS.title, key: FANCYTREE_ITEMS.OPERATION_CHARS.key, folder: true, expanded: true, children: [
		  {title: FANCYTREE_ITEMS.OPERATION_CHARS.TRAWL_SURVEY_HAULS.title, key: FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key, icon: false}
	    ]},
		{title: FANCYTREE_ITEMS.SPECIMENS.title, key: FANCYTREE_ITEMS.SPECIMENS.key, folder: true, expanded: true, children: [
		  {title: FANCYTREE_ITEMS.HOOK_LINE.title, key: FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, icon: false},
			{title: FANCYTREE_ITEMS.TRAWL.title, key: FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, icon: false}
	    ]},
		{title: FANCYTREE_ITEMS.SAMPLING_STATIONS_GRIDS.title, key: FANCYTREE_ITEMS.SAMPLING_STATIONS_GRIDS.key, folder: true, expanded: true, children: [
		
	     {title: FANCYTREE_ITEMS.SAMPLING_STATIONS_GRIDS.VESSEL_TRANSECTS.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.VESSEL_TRANSECTS.key, data:{layer:acousticsVesselTransectsLayer ,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.VESSEL_TRANSECTS.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.VESSEL_TRANSECTS.mapServices}, icon: false},
			{title: FANCYTREE_ITEMS.HOOK_LINE.title, key: FANCYTREE_ITEMS.HOOK_LINE.SAMPLING_SITES.key, icon: false},
			{title: FANCYTREE_ITEMS.TRAWL.title, key: FANCYTREE_ITEMS.TRAWL.STATION_GRID.key, data:{layer:trawlSurveyStationGridLayer  ,url:FANCYTREE_ITEMS.TRAWL.STATION_GRID.url, mapServices:FANCYTREE_ITEMS.TRAWL.STATION_GRID.mapServices}, icon: false}
	    ]},
		{title: FANCYTREE_ITEMS.SONAR_DATA.title, key: FANCYTREE_ITEMS.SONAR_DATA.key, folder: true, expanded: true, children: [
		
		  {title: FANCYTREE_ITEMS.SONAR_DATA.ACOUSTICS_HAKE_SURVEY.title, key: FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.key, data:{layer:acousticsSonarDataLayer,url:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.url, mapServices:FANCYTREE_ITEMS.ACOUSTICS_HAKE_SURVEY.SONAR_DATA.mapServices}, icon: false}	   
		  ]},

		{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.key, folder: true, expanded: true, children: [
		  {title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.key, data:{layer:spatialReferencesBathymetricCountoursLayer  ,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.BATHYMETRIC_CONTOURS.mapServices}, icon: false},
		{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.key, data:{layer:spatialReferencesMarineProtectedAreasLayer,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.MARINE_PROTECTED_AREAS.mapServices}, icon: false},
		{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.key, data:{layer:spatialReferencesNMFSTrawlRCALayer,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.NMFS_TRAWL_RCA.mapServices}, icon: false},

				{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.key, folder: true, expanded: true, children: [
				 {title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.key, data:{layer:spatialReferencesRegulatoryBoundariesPFMCLandmarksLayer,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.PFMC_LANDMARKS.mapServices}, icon: false},
			{title: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.title, key: FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.key, data:{layer:spatialReferencesRegulatoryBoundariesINPFCAreasLayer ,url:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.url, mapServices:FANCYTREE_ITEMS.SPATIAL_REFERENCES.REGULATORY_BOUNDARIES.INPFC_AREAS.mapServices}, icon: false}
				]},	
		]}
		
		
	  ],
	  checkbox: true,
	  selectMode:3
	});


/*********************************************************************************************************************************************
	FancyTree helper functions
**********************************************************************************************************************************************/
/*
    function setFancytreeItemCount(fancytreeItemProgram, fancytreeItemData,mapCount,totalCount) {


				if(totalCount!=0)
		{
				$("#layers").fancytree("getTree").getNodeByKey(fancytreeItemProgram.key).setTitle(fancytreeItemProgram.title+' &nbsp;&nbsp;&nbsp;'+mapCount+'/'+totalCount);
				$("#layers-content").fancytree("getTree").getNodeByKey(fancytreeItemProgram.key).setTitle(fancytreeItemData.title+' &nbsp;&nbsp;&nbsp;'+mapCount+'/'+totalCount);
				
		}
						//$("#layers").fancytree("getTree").getNodeByKey(fancytreeItem.key).setTitle(fancytreeItem.title+' &nbsp;&nbsp;&nbsp;'+mapCount+'/'+totalCount);
				//$(currentFancyTree).fancytree("getTree").getNodeByKey(fancytreeItem.key).setTitle(fancytreeItem.title+' &nbsp;&nbsp;&nbsp;'+mapCount+'/'+totalCount);
				
				else
		{
						$("#layers").fancytree("getTree").getNodeByKey(fancytreeItemProgram.key).setTitle(fancytreeItemProgram.title);
							$("#layers-content").fancytree("getTree").getNodeByKey(fancytreeItemProgram.key).setTitle(fancytreeItemData.title);
		}

		//			$(currentFancyTree).fancytree("getTree").getNodeByKey(fancytreeItem.key).setTitle(fancytreeItem.title);
					//	$("#layers").fancytree("getTree").getNodeByKey(fancytreeItem.key).setTitle(fancytreeItem.title);
	}
*/
	//check the fancy tree checkbox on both groups
	//if set = true, check the box, if set=false, uncheck
    function setFancytreeItem(fancytreeItem, set) {
				$("#layers").off("fancytreeselect");
				$("#layers-content").off("fancytreeselect");

				$("#layers").fancytree("getTree").getNodeByKey(fancytreeItem.key).setSelected(set);
				$("#layers-content").fancytree("getTree").getNodeByKey(fancytreeItem.key).setSelected(set);

				//Copy the ArcGIS layer to the corresponding group's layer
				if($("#layers").fancytree("getTree").getNodeByKey(fancytreeItem.key).data.layer==null)
					$("#layers").fancytree("getTree").getNodeByKey(fancytreeItem.key).data.layer = $("#layers-content").fancytree("getTree").getNodeByKey(fancytreeItem.key).data.layer;
				else
					$("#layers-content").fancytree("getTree").getNodeByKey(fancytreeItem.key).data.layer = $("#layers").fancytree("getTree").getNodeByKey(fancytreeItem.key).data.layer;
				

				$("#layers").on("fancytreeselect", fancyTreeHandler);
				$("#layers-content").on("fancytreeselect", fancyTreeHandler);
	}

/*********************************************************************************************************************************************
	FancyTree layer event handlers/functions
**********************************************************************************************************************************************/

	$("#layers").on("fancytreeselect", fancyTreeHandler);
	$("#layers-content").on("fancytreeselect", fancyTreeHandler);


	//This function shows/hides ArcGIS layers based on
	//fancytree item keys and their correspsonding data property
	function fancyTreeArcGISHandler(node){ 

		if( node.data.url )
			{ 
				if( node.isSelected()	 )
				{		
					setFancytreeItem(node,true);

					if( node.data.layer  != null )
						layers.add(node.data.layer );
					else
						node.data.layer  = layers.addImageryProvider(new Cesium.ArcGisMapServerImageryProvider({
							url : node.data.url,
							layers:node.data.mapServices[0]
								   
						}));

					if( self.checkedLayers.indexOf(node.key) < 0 )
						self.checkedLayers.push(node.key);

				}
				else if ( self.checkedLayers.indexOf(node.key) > -1 )
				{	
					setFancytreeItem(node,false);
					layers.remove(node.data.layer ,false);
					self.checkedLayers.splice(self.checkedLayers.indexOf(node.key), 1);
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

			var endMonth = self.cycleStartDate.getMonth()+1;
			var endDay = self.cycleStartDate.getDate();

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

					 $scope.$apply(function () {
						$scope.hookLineSpecimensBtnShow = true;
					});

					setFancytreeItem(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS,true);
							
					showDatatable("#hook_line_specimens_table");

					$( "#radio5" ).prop( "checked", true );
					$( "#radio5" ).button( "refresh" );


					//console.log("Hook and line specimen selected");
					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key);
					
						var j_species_codes = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++) 
								j_species_codes.push(self.selectedSpecies[i].scientific_name);

						
						getPlotHookLineSpecimens(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key) > -1 )
				{

						hookLineSpecimenCanceler.resolve();

						 $scope.$apply(function () {
							$scope.hookLineSpecimensBtnShow = false;
						});
								
						layerUncheckCleanup(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS);
						
						//remove all species datatable rows
						hookLineSpecimensDataTable.clear().draw();
						$("#hook_line_specimens_table").parents('div.dataTables_wrapper').first().hide();

						$( "#radio5" ).prop( "checked", false );
						$( "#radio5" ).button( "refresh" );

				}

			}


			if ( data.node.key==FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key || data.node.key==FANCYTREE_ITEMS.OBSERVER.key )
			{

				if( data.node.isSelected()	 )
				{		
					observerCatchCanceler = $q.defer();

					 $scope.$apply(function () {
						$scope.observerCatchBtnShow = true;
					});

					setFancytreeItem(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS,true);
							
					showDatatable("#observer_catch_table");


					$( "#radio7" ).prop( "checked", true );
					$( "#radio7" ).button( "refresh" );


					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key);
					
						var j_species_codes = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++) 
								j_species_codes.push(self.selectedSpecies[i].scientific_name);

						
						getObserverCatch(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key) > -1 )
				{

						observerCatchCanceler.resolve();

						 $scope.$apply(function () {
							$scope.observerCatchBtnShow = false;
						});
								
						self.checkedLayers.splice(self.checkedLayers.indexOf(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key), 1);

						setFancytreeItem(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS,false);

						//remove all species datatable rows
						observerCatchDataTable.clear().draw();
						$("#observer_catch_table").parents('div.dataTables_wrapper').first().hide();

						$( "#radio7" ).prop( "checked", false );
						$( "#radio7" ).button( "refresh" );

				}

			}



			if ( data.node.key==FANCYTREE_ITEMS.HOOK_LINE.CATCH.key || data.node.key==FANCYTREE_ITEMS.HOOK_LINE.key )
			{			
				if( data.node.isSelected()	 )
				{		
					hookLineCatchCanceler = $q.defer();

					 $scope.$apply(function () {
						$scope.hookLineCatchBtnShow = true;
					});
		
					showDatatable("#hook_line_catch_table");

					$( "#radio6" ).prop( "checked", true );
					$( "#radio6" ).button( "refresh" );

					setFancytreeItem(FANCYTREE_ITEMS.HOOK_LINE.CATCH,true);


					//console.log("Hook and line specimen selected");
					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key);
					
						var j_species_codes = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++) 
								j_species_codes.push(self.selectedSpecies[i].scientific_name);

						
						getPlotHookLineCatch(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key) > -1 )
				{
						hookLineCatchCanceler.resolve();

						 $scope.$apply(function () {
							$scope.hookLineCatchBtnShow = false;
						});
								
						layerUncheckCleanup(FANCYTREE_ITEMS.HOOK_LINE.CATCH);
						
						//remove all species datatable rows
						hookLineCatchDataTable.clear().draw();
						$("#hook_line_catch_table").parents('div.dataTables_wrapper').first().hide();

						$( "#radio6" ).prop( "checked", false );
						$( "#radio6" ).button( "refresh" );

				}

			}


			if ( data.node.key==FANCYTREE_ITEMS.TRAWL.SPECIMENS.key || data.node.key==FANCYTREE_ITEMS.TRAWL.key )
			{
				if( data.node.isSelected()	 )
				{	
					 trawlSpecimensCanceler = $q.defer();

					 $scope.$apply(function () {
						$scope.trawlSpecimensBtnShow = true;
					});
							
					setFancytreeItem(FANCYTREE_ITEMS.TRAWL.SPECIMENS,true);

					showDatatable("#trawl_specimens_table");

					$( "#radio4" ).prop( "checked", true );
					$( "#radio4" ).button( "refresh" );


					//console.log("Individual Organisms selected");
					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key);
					
						var j_species_codes = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++) 
								j_species_codes.push(self.selectedSpecies[i].scientific_name);

						getPlotTrawlSpecimens(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key) > -1 )
				{	
					trawlSpecimensCanceler.resolve();

					 $scope.$apply(function () {
						$scope.trawlSpecimensBtnShow = false;
					});
							
					layerUncheckCleanup(FANCYTREE_ITEMS.TRAWL.SPECIMENS);

					//remove all species datatable rows
					trawlSpecimensDataTable.clear().draw();

					$("#trawl_specimens_table").parents('div.dataTables_wrapper').first().hide();

					$( "#radio4" ).prop( "checked", false );
					$( "#radio4" ).button( "refresh" );


				}//end if( data.node.isSelected() )

			} //end if (data.node.title=='Individual Organisms' || data.node.title=='Trawl')



			if (data.node.key==FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key || data.node.key==FANCYTREE_ITEMS.TRAWL.key)
			{
				if( data.node.isSelected() )
				{	

					trawlHaulCharsCanceler = $q.defer();

					$scope.$apply(function () {
						$scope.trawlHaulCharsBtnShow = true;
					});

					setFancytreeItem(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS,true);
					 
					showDatatable("#trawl_haul_chars_table");


					$( "#radio3" ).prop( "checked", true );
					$( "#radio3" ).button( "refresh" );

					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key);
						getPlotTrawlHaulChars(startDateyyyymmdd,endDateyyyymmdd);
					}
				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key) > -1 )
				{
					trawlHaulCharsCanceler.resolve();
					$scope.$apply(function () {
						$scope.trawlHaulCharsBtnShow = false;
					});

					layerUncheckCleanup(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS);

					//remove all species datatable rows
					trawlHaulCharsDataTable.clear().draw();

					$("#trawl_haul_chars_table").parents('div.dataTables_wrapper').first().hide();

					$( "#radio3" ).prop( "checked", false );
					$( "#radio3" ).button( "refresh" );

				
				}//end if( data.node.isSelected() )

			} //end if (data.node.title==FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key || data.node.title=='Trawl')



			if ( data.node.key==FANCYTREE_ITEMS.TRAWL.CATCH.key || data.node.key==FANCYTREE_ITEMS.TRAWL.key )
			{
				if( data.node.isSelected()	 )
				{	

					trawlCatchCanceler = $q.defer();
					$scope.$apply(function () {
						$scope.trawlCatchBtnShow = true;
					});

					setFancytreeItem(FANCYTREE_ITEMS.TRAWL.CATCH,true);

					showDatatable("#trawl_catch_table");


					$( "#radio2" ).prop( "checked", true );
					$( "#radio2" ).button( "refresh" );

					//console.log("Individual Organisms selected");
					if( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.CATCH.key) < 0 )
					{
						self.checkedLayers.push(FANCYTREE_ITEMS.TRAWL.CATCH.key);
					
						var j_species_scientific_names = [];

						if (self.selectedSpecies!=null && self.selectedSpecies!='')
						 for (var i = 0; i < self.selectedSpecies.length; i++) 
								j_species_scientific_names.push(self.selectedSpecies[i].scientific_name);

						getPlotTrawlCatch(j_species_scientific_names,startDateyyyymmdd,endDateyyyymmdd);
					}

				}
				else if ( self.checkedLayers.indexOf(FANCYTREE_ITEMS.TRAWL.CATCH.key) > -1 )
				{


					trawlCatchCanceler.resolve();

					$scope.$apply(function () {
						$scope.trawlCatchBtnShow = false;
					});

					layerUncheckCleanup(FANCYTREE_ITEMS.TRAWL.CATCH);

					//remove all species datatable rows
					trawlCatchDataTable.clear().draw();
					$("#trawl_catch_table").parents('div.dataTables_wrapper').first().hide();

					$( "#radio2" ).prop( "checked", false );
					$( "#radio2" ).button( "refresh" );


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

		//remove any point on the map that the user might have clicked on
		viewer.entities.removeById(fancyTreeItem.key);

		//remove all point primitives from the map
		showHidePrimitives(fancyTreeItem.key, null, false); 
		
		//uncheck the corresponding group layer
		setFancytreeItem(fancyTreeItem,false);
	}


/*********************************************************************************************************************************************
	Datatable initialization
**********************************************************************************************************************************************/

	var datatableScrollerHeight = screen.height-370;
	var observerCatchDataTable = $('#observer_catch_table').DataTable( {
			rowId: 'rowId',
	 dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'print'
        ],

     deferRender:    true,
            scrollY:        datatableScrollerHeight,
          //  scrollCollapse: true,
               scroller:true,
		 scrollX: true ,
		 lengthChange: false,
        select: {
            style: 'single'
        },
		
    columns: [
        { data: 'data.taxonomy_dim$scientific_name',title: 'Scientific Name', defaultContent: "" },
		{ data: 'data.taxonomy_dim$common_name',title: 'Common Name', defaultContent: "" },
		{ data: 'data.season_year',title: 'Year', defaultContent: "" },
		{ data: 'data.report_category',title: 'Report Category', defaultContent: "" },
		{ data: 'data.catch_updated_date',title: 'Catch Updated Date', defaultContent: "" },
		{ data: 'data.discard_weight_est_lbs',title: 'Discard Weight Est. (lbs)', defaultContent: "" },
		{ data: 'data.discard_count_est',title: 'Discard Count Est.', defaultContent: "" }
    ]
	} );



 	var trawlSpecimensDataTable = $('#trawl_specimens_table').DataTable( {
			rowId: 'rowId',

	 dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'print'
        ],

     deferRender:    true,
            scrollY:        datatableScrollerHeight,
          //  scrollCollapse: true,
               scroller:true,
		 scrollX: true ,
		 lengthChange: false,
        select: {
            style: 'single'
        },
    columns: [
        { data: 'data.date_dim$yyyymmdd',title: 'Date (YYYYMMDD)', defaultContent: "" },
		{ data: 'data.sampling_start_time_dim$hh24miss',title: 'Sampling Start Time (HHMMSS)', defaultContent: "" },
		{ data: 'data.sampling_end_time_dim$hh24miss',title: 'Sampling End Time (HHMMSS)', defaultContent: "" },
		{ data: 'data.operation_dim$vessel',title: 'Vessel', defaultContent: "" },
		{ data: 'data.operation_dim$pass',title: 'Pass', defaultContent: "" },
		{ data: 'data.operation_dim$leg',title: 'Leg', defaultContent: "" },
		{ data: 'data.operation_dim$operation_id',title: 'Haul ID', defaultContent: "" },
		{ data: 'data.field_identified_taxonomy_dim$scientific_name',title: 'Field Scientific Name', defaultContent: "" },	
		{ data: 'data.best_available_taxonomy_dim$scientific_name',title: 'Best Available Scientific Name', defaultContent: "" },
		{ data: 'data.best_available_taxonomy_dim$common_name',title: 'Best Available Common Name', defaultContent: "" },
		{ data: 'data.haul_latitude_dim$latitude_in_degrees',title: 'Latitude', defaultContent: "" },
		{ data: 'data.haul_longitude_dim$longitude_in_degrees',title: 'Longitude', defaultContent: "" },
		{ data: 'data.target_station_design_dim$station_code',title: 'Station Code', defaultContent: "" },
		{ data: 'data.sex_dim$sex',title: 'Sex', defaultContent: "" },
		{ data: 'data.length_cm',title: 'Length (cm)', defaultContent: "" },
		{ data: 'data.age_years',title: 'Age', defaultContent: "" },
		{ data: 'data.weight_kg',title: 'Weight (kg)', defaultContent: "" },
		{ data: 'data.seafloor_depth_dim$depth_meters',title: 'Depth (m)', defaultContent: "" }
    ]
	} );




 	var trawlHaulCharsDataTable = $('#trawl_haul_chars_table').DataTable( {
	 dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'print'
        ],
     deferRender:    true,
            scrollY:        datatableScrollerHeight,
          //  scrollCollapse: true,
               scroller:true,
		 scrollX: true ,
		 lengthChange: false,
        select: {
            style: 'single'
        },
    columns: [
		{ data: 'data.date_dim$yyyymmdd',title: 'Date-Time (YYYYmmdd)', defaultContent: "" },
		{ data: 'data.sampling_start_time_dim$hh24miss',title: 'Sampling Start Time (HHMMSS)', defaultContent: "" },
		{ data: 'data.sampling_end_time_dim$hh24miss',title: 'Sampling End Time (HHMMSS)', defaultContent: "" },
        { data: 'data.operation_dim$project_name',title: 'Project', defaultContent: "" },
		{ data: 'data.operation_dim$vessel',title: 'Vessel', defaultContent: "" },
		{ data: 'data.operation_dim$pass',title: 'Pass', defaultContent: "" },
		{ data: 'data.operation_dim$leg',title: 'Leg', defaultContent: "" },
		{ data: 'data.operation_dim$operation_id',title: 'Haul ID', defaultContent: "" },
        { data: 'data.operation_dim$performance_result',title: 'Haul Performance', defaultContent: "" },
		{ data: 'data.haul_latitude_dim$latitude_in_degrees',title: 'Haul Latitude', defaultContent: "" },
		{ data: 'data.haul_longitude_dim$longitude_in_degrees',title: 'Haul Longitude', defaultContent: "" },
		{ data: 'data.vessel_start_lat_dd',title: 'Vessel Start Latitude', defaultContent: "" },
		{ data: 'data.vessel_start_lon_dd',title: 'Vessel Start Longitude', defaultContent: "" },
		{ data: 'data.vessel_end_lat_dd',title: 'Vessel End Latitude', defaultContent: "" },
		{ data: 'data.vessel_end_lon_dd',title: 'Vessel End Longitude', defaultContent: "" },
		{ data: 'data.gear_start_lat_dd',title: 'Gear Start Latitude', defaultContent: "" },
		{ data: 'data.gear_start_lon_dd',title: 'Gear Start Longitude', defaultContent: "" },
		{ data: 'data.gear_end_lat_dd',title: 'Gear End Latitude', defaultContent: "" },
		{ data: 'data.gear_end_lon_dd',title: 'Gear End Longitude', defaultContent: "" },
		{ data: 'data.area_swept_ha_der',title: 'Area Swept (ha)', defaultContent: "" },
		{ data: 'data.net_height_m_der',title: 'Net Height (m)', defaultContent: "" },
		{ data: 'data.net_width_m_der',title: 'Net Width (m)', defaultContent: "" },
		{ data: 'data.door_width_m_der',title: 'Door Width (m)', defaultContent: "" },
		{ data: 'data.temperature_at_gear_c_der',title: 'Temperate at Gear (c)', defaultContent: "" },
		{ data: 'data.temperature_at_surface_c_der',title: 'Temperature at Surface (c)', defaultContent: "" },
		{ data: 'data.seafloor_depth_m_der',title: 'Sea Floor Depth (m)', defaultContent: "" },
		{ data: 'data.turbidity_ntu_der',title: 'Turbitity (ntu)', defaultContent: "" },
		{ data: 'data.salinity_at_gear_psu_der',title: 'Salinity at Gear (psu)', defaultContent: "" },
		{ data: 'data.o2_at_gear_ml_per_l_der',title: 'Dissolved Oxygen (ml/l)', defaultContent: "" },
		{ data: 'data.vertebrate_weight_kg',title: 'Vertebrate Weight (kg)', defaultContent: "" },
		{ data: 'data.invertebrate_weight_kg',title: 'Invertebrate Weight (kg)', defaultContent: "" },
		{ data: 'data.nonspecific_organics_weight_kg',title: 'Non-specific Organics Weight (kg)', defaultContent: "" },
		{ data: 'data.fluorescence_at_surface_mg_per_m3_der',title: 'Fluorescence at Surface (mg/m^3)', defaultContent: "" }
    ]
	} );



 	var hookLineSpecimensDataTable = $('#hook_line_specimens_table').DataTable( {
	 rowId: 'rowId',
	 dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'print'
        ],
     deferRender:    true,
            scrollY:        datatableScrollerHeight,
          //  scrollCollapse: true,
               scroller:true,
		 scrollX: true ,
		 lengthChange: false,
	
        select: {
            style: 'single'
        },
    columns: [
        { data: 'data.operation_dim$project_name',title: 'Project', defaultContent: "" },
		{ data: 'data.operation_dim$leg',title: 'Leg', defaultContent: "" },
		{ data: 'data.date_dim$full_date',title: 'Date (YYYYMMDD)', defaultContent: "" },
		{ data: 'data.drop_time_dim$hh24miss',title: 'Drop Time (HHMMSS)', defaultContent: "" },
        { data: 'data.best_available_taxonomy_dim$scientific_name',title: 'Best Available Scientific Name', defaultContent: "" },
		{ data: 'data.best_available_taxonomy_dim$common_name',title: 'Best Available Common Name', defaultContent: "" },
		{ data: 'data.operation_dim$vessel',title: 'Vessel', defaultContent: "" },
		{ data: 'data.site_dim$area_name',title: 'Area', defaultContent: "" },
		{ data: 'data.site_dim$site_number',title: 'Site Number', defaultContent: "" },
		{ data: 'data.drop_latitude_dim$latitude_in_degrees',title: 'Drop Latitude', defaultContent: "" },
		{ data: 'data.drop_longitude_dim$longitude_in_degrees',title: 'Drop Longitude', defaultContent: "" },
		{ data: 'data.drop_sounder_depth_dim$depth_meters',title: 'Drop Depth (m)', defaultContent: "" },
		{ data: 'data.hook_dim$hook_number',title: 'Hook Number', defaultContent: "" },
		{ data: 'data.hook_dim$hook_result',title: 'Hook Result', defaultContent: "" },
		{ data: 'data.sex_dim$sex',title: 'Sex', defaultContent: "" },
		{ data: 'data.length_cm',title: 'Length (cm)', defaultContent: "" },
		{ data: 'data.age_years',title: 'Age', defaultContent: "" },
		{ data: 'data.weight_kg',title: 'Weight (kg)', defaultContent: "" },
		{ data: 'data.otolith_number',title: 'Otolith Number', defaultContent: "" },
		{ data: 'data.fin_clip_number',title: '	Fin Clip Number', defaultContent: "" }
		
			

    ]
	} );



	var hookLineCatchDataTable = $('#hook_line_catch_table').DataTable( {
	 rowId: 'rowId',
	 dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'print'
        ],
     deferRender:    true,
            scrollY:        datatableScrollerHeight,
          //  scrollCollapse: true,
               scroller:true,
		 scrollX: true ,
		 lengthChange: false,
	
        select: {
            style: 'single'
        },
    columns: [
        { data: 'data.project_name',title: 'Project', defaultContent: "" },
		{ data: 'data.leg',title: 'Leg', defaultContent: "" },
		{ data: 'data.date_dim$full_date',title: 'Date-Time (UTC)', defaultContent: "" },
        { data: 'data.best_available_taxonomy_dim$scientific_name',title: 'Best Available Scientific Name', defaultContent: "" },
        { data: 'data.best_available_taxonomy_dim$common_name',title: 'Best Available Common Name', defaultContent: "" },
		{ data: 'data.vessel',title: 'Vessel', defaultContent: "" },
		{ data: 'data.site_dim$site_latitude_dd',title: 'Latitude', defaultContent: "" },
		{ data: 'data.site_dim$site_longitude_dd',title: 'Longitude', defaultContent: "" },
		{ data: 'data.total_catch_numbers',title: '	Total Fish Caught per Site', defaultContent: "" },
		{ data: 'data.total_catch_wt_kg',title: 'Total Catch Weight per Site (Kg)', defaultContent: "" },
		{ data: 'data.site_dim$area_name',title: 'Area', defaultContent: "" },
		{ data: 'data.site_dim$site_number',title: 'Site Number', defaultContent: "" },
		{ data: 'data.wave_height_m',title: 'Wave Height (m)', defaultContent: "" },
		{ data: 'data.swell_direction_mag',title: 'Swell Direction (deg)', defaultContent: "" },
		{ data: 'data.swell_height_m',title: 'Swell Height (m)', defaultContent: "" },
		{ data: null,title: 'Sea Surface Temperature (c)', //defaultContent: "" ,
			 render: function ( data, type, row ) {
				return (Math.round(data.data.sea_surface_temp_c * 10)/10 );
                 } },
		{ data: 'data.ctd_sounder_depth_m',title: 'Sounder Depth (CTD Drop) (m)', defaultContent: "" },
		{ data: 'data.ctd_on_bottom_measure_depth_dim$depth_meters',title: 'CTD Measured Depth (m)', defaultContent: "" },
	    { data: 'data.ctd_on_bottom_temp_c',title: 'CTD Bottom Temperature (c)', defaultContent: "" },
		{ data: 'data.ctd_on_bottom_salinity_psu',title: 'CTD Salinity (psu)', defaultContent: "" },
		{ data: 'data.ctd_on_bottom_disolved_oxygen_sbe43_ml_per_l',title: 'CTD Dissolved Oxygen - SBE43 (ml/l)', defaultContent: "" },
		{ data: 'data.ctd_on_bottom_disolved_oxygen_aanderaa_ml_per_l',title: 'CTD Dissolved Oxygen - Aanderaa (ml/l)', defaultContent: "" }
    ]
	} );

	var trawlCatchDataTable = $('#trawl_catch_table').DataTable( {
	rowId: 'rowId',
	 dom: 'Bfrtip',

        buttons: [
            'copy', 'csv', 'excel', 'print'
        ],
     deferRender:    true,
            scrollY:        datatableScrollerHeight,
          //  scrollCollapse: true,
               scroller:true,
		 scrollX: true ,
		 lengthChange: false,
		
        select: {
            style: 'single'
        },

    columns: [

		{ data: 'data.date_dim$full_date',title: 'Date-Time (YYYYmmdd)', defaultContent: "" },
		{ data: 'data.sampling_start_time_dim$hh24miss',title: 'Sampling Start Time (HHMMSS)' , defaultContent: ""},
		{ data: 'data.sampling_end_time_dim$hh24miss',title: 'Sampling End Time (HHMMSS)', defaultContent: "" },
        { data: 'data.operation_dim$vessel',title: 'Vessel', defaultContent: "" },
		{ data: 'data.operation_dim$pass',title: 'Pass', defaultContent: "" },
		{ data: 'data.operation_dim$leg',title: 'Leg', defaultContent: "" },
		{ data: 'data.operation_dim$operation_id',title: 'Haul ID', defaultContent: "" },
		{ data: 'data.haul_latitude_dim$latitude_in_degrees',title: 'Latitude', defaultContent: "" },
		{ data: 'data.haul_longitude_dim$longitude_in_degrees',title: 'Longitude', defaultContent: "" },
		{ data: 'data.target_station_design_dim$station_code',title: 'Station Code', defaultContent: "" },
		{ data: 'data.field_identified_taxonomy_dim$scientific_name',title: 'Field Scientific Name', defaultContent: "" },
		{ data: 'data.best_available_taxonomy_dim$scientific_name',title: 'Best Available Scientific Name', defaultContent: "" },
		{ data: 'data.best_available_taxonomy_dim$common_name',title: 'Best Available Common Name', defaultContent: "" },
		{ data: 'data.subsample_wt_kg',title: 'Subsample Weight (kg)', defaultContent: "" },
		{ data: 'data.subsample_count',title: 'Subsample Count', defaultContent: "" },
		{ data: 'data.total_catch_wt_kg',title: 'Total Weight (kg)', defaultContent: "" },
		{ data: 'data.total_catch_numbers',title: 'Total Count', defaultContent: "" },
		{ data: 'data.taxonomy_observation_detail_dim$measurement_procurement',title: 'Weight Method', defaultContent: "" },
		{ data: 'data.statistical_partition_dim$statistical_partition_value',title: 'Statistical Partition Value', defaultContent: "" },
		{ data: 'data.operation_dim$performance_result',title: 'Performance', defaultContent: "" },
		{ data: 'data.seafloor_depth_dim$depth_meters',title: 'Seafloor Depth (m)', defaultContent: "" },
		{ data: 'data.cpue_kg_per_ha_der',title: 'CPUE Kg/Ha Derived', defaultContent: "" },
		{ data: 'data.operation_dim$project_name',title: 'Project Name', defaultContent: "" },
		{ data: 'data.target_station_design_dim$date_stn_invalid_for_trawl_whid',title: 'Date Station Invalid', defaultContent: "" }
		


		
    ]
	} );

	
	//hide all datatables on page load
	showDatatable();

/*********************************************************************************************************************************************
	Datatable to CesiumJS map functions
**********************************************************************************************************************************************/

   /**
     * This function is used to select a point on the map
	 * corresponding to the datatable row selected
     */
    function selectMapPoint(e, dt, type, indexes, layer, datatable, scientificName) {
		if (!pickingMapInput)
		{
			datatable.rows().nodes().to$().removeClass('selected');
			datatable.rows( indexes ).nodes().to$().addClass('selected');
			var index  = datatable.row( indexes ).id().substring(datatable.row( indexes ).id().length-1,datatable.row( indexes ).id().length);

			var primitiveCollection = scene.primitives;

			 for (var i = 0; i < primitiveCollection.length; i++) {
				   var pointPrimitives = primitiveCollection.get(i);

					for (var j = 0; j < pointPrimitives.length; j++) {
					   if(pointPrimitives.get(j).id.layer==layer.key && pointPrimitives.get(j).id.index==index && pointPrimitives.get(j).id.scientificName==scientificName)   
						{		var cartographic =  Cesium.Ellipsoid.WGS84.cartesianToCartographic(pointPrimitives.get(j).position);
					   
								viewer.entities.removeAll();

								var entity = new Cesium.Entity({
												name: scientificName+' '+index,
												position : Cesium.Cartesian3.fromDegrees(Cesium.Math.toDegrees(cartographic.longitude), Cesium.Math.toDegrees(cartographic.latitude)),
												id : layer.key,

												scaleByDistance : new Cesium.NearFarScalar(1.5e2, 1.0, 1.5e7, 0.5),
												point : {
													pixelSize : 10,
													color : randomColor.get(scientificName)
												}
											});

								viewer.entities.add(entity);
								viewer.selectedEntity = entity;

						}
					}
			   }
		}
	}
	

	trawlHaulCharsDataTable.on( 'select', function ( e, dt, type, indexes ) {
		if (!pickingMapInput)
		{
			trawlHaulCharsDataTable.rows().nodes().to$().removeClass('selected');
			trawlHaulCharsDataTable.rows( indexes ).nodes().to$().addClass('selected');
			
			//remove any other selected point on the map
			viewer.entities.removeAll();

			var primitivePoint = scene.primitives.get( layerToPrimitiveIndexDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key) ).get( indexes[0] );
			var cartographic =  Cesium.Ellipsoid.WGS84.cartesianToCartographic(primitivePoint.position);

			var entity = new Cesium.Entity({
							name: primitivePoint.id.vessel,
							position : Cesium.Cartesian3.fromDegrees(Cesium.Math.toDegrees(cartographic.longitude), Cesium.Math.toDegrees(cartographic.latitude)),
							id : 'CurrrentPoint',

							scaleByDistance : new Cesium.NearFarScalar(1.5e2, 1.0, 1.5e7, 0.5),
							point : {
								pixelSize : 10,
								color : randomColor.get(primitivePoint.id.vessel)
							}
						});

			viewer.entities.add(entity);
			viewer.selectedEntity = entity;

		}//end if (!pickingMapInput)

	} );

	
	trawlSpecimensDataTable.on( 'select', function ( e, dt, type, indexes ) {

		var scientificName  = trawlSpecimensDataTable.row( indexes ).data().data.best_available_taxonomy_dim$scientific_name;
		selectMapPoint(e, dt, type, indexes, FANCYTREE_ITEMS.TRAWL.SPECIMENS, trawlSpecimensDataTable, scientificName);


	} );


	trawlCatchDataTable.on( 'select', function ( e, dt, type, indexes ) {
		
		var scientificName  = trawlCatchDataTable.row( indexes ).data().data.best_available_taxonomy_dim$scientific_name;
		selectMapPoint(e, dt, type, indexes, FANCYTREE_ITEMS.TRAWL.CATCH, trawlCatchDataTable, scientificName);

	} );


	hookLineSpecimensDataTable.on( 'select', function ( e, dt, type, indexes ) {

		var scientificName  = hookLineSpecimensDataTable.row( indexes ).data().data.taxonomy_dim$scientific_name;
		selectMapPoint(e, dt, type, indexes, FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS, hookLineSpecimensDataTable, scientificName);

	} );

	hookLineCatchDataTable.on( 'select', function ( e, dt, type, indexes ) {

		var scientificName  = hookLineCatchDataTable.row( indexes ).data().data.taxonomy_dim$scientific_name;
		selectMapPoint(e, dt, type, indexes, FANCYTREE_ITEMS.HOOK_LINE.CATCH, hookLineCatchDataTable, scientificName);

	} );


/*********************************************************************************************************************************************
	Show/hide point primitive functions
**********************************************************************************************************************************************/

	/**
     * Reduce the index count for all species in all layers by 1
	 * if the index value is greater than parameter index
	 * This is because when a primitive collection is deleted, all the indices 
	 * in scene.primitives shift by 1 (meaning subtract by 1)
     */
	
	function reduceIndicesBy1(index){ 

		for(var i=0; i<layerToPrimitiveIndexDict.keys.length; i++)
		{
			var speciesIndicesDict = layerToPrimitiveIndexDict.get(layerToPrimitiveIndexDict.keys[i]);

			for(var j=0; j<speciesIndicesDict.keys.length; j++)
			{
				if(speciesIndicesDict.values[j]>index)
					speciesIndicesDict.values[j]=speciesIndicesDict.values[j]-1;

			}
		}
	
	}

    /**
     * Check if an existing species point primitives data exists for a particular layer to avoid an API call.
	 * If show = true, then the points are shown, otherwise, the points are hidden
	 * returns the true if layer/species combination exists, otherwise returns false 
     */
	function showHidePrimitives(layer, scientificName, show){ 
		var pointPrimitivesExists = false;
		var speciesNoBlanks = null;
		
		if( scientificName!= null)
			speciesNoBlanks = (scientificName).replace(/\s+/g, '');

//		console.log('Calling showHidePrimitives with layer='+layer+' scientificName with blanks removed='+speciesNoBlanks+' show='+show);

		if( !show && layerToPrimitiveIndexDict.has(layer) )
		{
			if( layerToPrimitiveIndexDict.get(layer).has(speciesNoBlanks) )
			{
				//console.log(scene.primitives);
				var speciesIndex = layerToPrimitiveIndexDict.get(layer).get(speciesNoBlanks);

				//remove PointPrimitiveCollection from the scene
				scene.primitives.remove(scene.primitives.get(speciesIndex));

				layerToPrimitiveIndexDict.get(layer).delete(speciesNoBlanks);
				
				//when the PointPrimitiveCollection is removede from the scene
				//all the remaining PointPrimitiveCollections after that collection
				//have their indices reduced by 1, hence the next function
				reduceIndicesBy1(speciesIndex);

				pointPrimitivesExists = true;
				//console.log(scene.primitives);

			}
			else if ( speciesNoBlanks == null )
			{
				var layerSpeciesIndices = layerToPrimitiveIndexDict.get(layer);
				for(var i=0; i<layerSpeciesIndices.keys.length; i++)
				{
					var speciesIndex = layerToPrimitiveIndexDict.get(layer).get(layerSpeciesIndices.keys[i]);
					scene.primitives.remove(scene.primitives.get(speciesIndex));
					reduceIndicesBy1(speciesIndex);

				}
				layerToPrimitiveIndexDict.get(layer).clear();
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
				pointPrimitivesExists = true;

				var primitives = layerToPrimitiveDict.get(layer).get(speciesNoBlanks);
				scene.primitives.add(primitives);
				layerToPrimitiveIndexDict.get(layer).set(speciesNoBlanks,scene.primitives.length-1);
			}
		
		}

//		console.log('In showHidePrimitives return '+pointPrimitivesExists);
		return pointPrimitivesExists;
	}





/*********************************************************************************************************************************************
	Handle species chip add/remove
**********************************************************************************************************************************************/

    /**
     * Remove any rows in layerDatatable table that contains the species removedSpecie and index (CSS ID which is "."+scientificName)
     */
    function removeSpeciesDatatable(layerDatatable, index, removedSpecie) {
		
			//remove specific catch datatable rows
			layerDatatable.rows( index ).remove().draw(); //this only removes 81 records because initially datatables only renders 81 records

			//the following loop removes any matched species (if there were more than 81 records)
			var removeIndices = [];

			layerDatatable.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
				 //rowId consists of scientifisName+i where i is a random number
				 //so strip away the i
				var speciesWithoutId = this.data().rowId.replace(/[0-9]/g, ''); 

				if( speciesWithoutId == removedSpecie )
					removeIndices.push(rowIdx);
			} );

			if(removeIndices.length>0)
				layerDatatable.rows(removeIndices).remove().draw();
    }

	$scope.$watchCollection('ctrl.selectedSpecies', function(newNames, oldNames) {

			var species_codes = [];
			var scientific_names = [];
			var removed_map_points = [];

			var removed_species = $(oldNames).not(newNames).get();  //species that were removed
			var added_species = $(newNames).not(oldNames).get()		//species that were added

			var startMonth = self.cycleStartDate.getMonth()+1;
			var startDay = self.cycleStartDate.getDate();

			var endMonth = self.cycleStartDate.getMonth()+1;
			var endDay = self.cycleStartDate.getDate();

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
					//console.log('removed_species[i].species='+removed_species[i].species_code);
					//var existingSpeciesDataSource = dataSourceExistsBySpecies(removed_species[i].species_code);
			//		console.log('removed_species[i].scientific_name='+removed_species[i].scientific_name);
					//var existingSpeciesDataSource = dataSourceExistsBySpecies(removed_species[i].scientific_name);


					var newSpeciesNoBlanks = (removed_species[i].scientific_name).replace(/\s+/g, ''); 
					var index =  '.'+newSpeciesNoBlanks;	



					var existingSpeciesData = showHidePrimitives(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key,removed_species[i].scientific_name,false);
					
					if (existingSpeciesData)
					{
							removeSpeciesDatatable(trawlSpecimensDataTable, index, newSpeciesNoBlanks);

							if(viewer.entities.getById(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key))
								if( viewer.entities.getById(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).name.indexOf(removed_species[i].scientific_name)>=0 )
									viewer.entities.removeAll();
					}




					existingSpeciesData = showHidePrimitives(FANCYTREE_ITEMS.TRAWL.CATCH.key,removed_species[i].scientific_name,false);
					
					if (existingSpeciesData)
					{
							removeSpeciesDatatable(trawlCatchDataTable, index, newSpeciesNoBlanks);

							if(viewer.entities.getById(FANCYTREE_ITEMS.TRAWL.CATCH.key))
								if( viewer.entities.getById(FANCYTREE_ITEMS.TRAWL.CATCH.key).name.indexOf(removed_species[i].scientific_name)>=0 )
									viewer.entities.removeAll();
					}




					var existingObserverCatchData = observerCatchDataTableDict.get( removed_species[i].scientific_name.replace(/\s+/g, '') );

					if (existingObserverCatchData)
					{

						var index =  '.'+(removed_species[i].scientific_name.replace(/\s+/g, ''));	

						observerCatchDataTable.rows( index ).remove().draw(); //this only removes 81 records because initially datatables only renders 81 records
						
						//the following loop removes any matched species (if there were more than 81 records)
						var removeIndices = [];

						observerCatchDataTable.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
							if( this.data().scientificName == removed_species[i].scientific_name )
								removeIndices.push(rowIdx);
						} );

						if(removeIndices.length>0)
							observerCatchDataTable.rows(removeIndices).remove().draw();				


					}

					existingSpeciesData = showHidePrimitives(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key,removed_species[i].scientific_name,false);
					
					if (existingSpeciesData)
					{
							removeSpeciesDatatable(hookLineSpecimensDataTable, index, newSpeciesNoBlanks);

							if(viewer.entities.getById(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key))
								if( viewer.entities.getById(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).name.indexOf(removed_species[i].scientific_name)>=0 )
									viewer.entities.removeAll();
					}


					existingSpeciesData = showHidePrimitives(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key,removed_species[i].scientific_name,false);
					
					if (existingSpeciesData)
					{
							removeSpeciesDatatable(hookLineCatchDataTable, index, newSpeciesNoBlanks);

							if(viewer.entities.getById(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key))
								if( viewer.entities.getById(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).name.indexOf(removed_species[i].scientific_name)>=0 )
									viewer.entities.removeAll();
					}

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
				getObserverCatch(species_codes,startDateyyyymmdd,endDateyyyymmdd);

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

		if(data[data.length-1].operation_dim$operation_id===undefined)
			data.pop();

		self.species = loadSpecies(data);
		$scope.disableSpeciesFilter = false;
	 });


/*********************************************************************************************************************************************
	Functions for API calls
**********************************************************************************************************************************************/

    /**
     * Get haul characteristics data from DB and plot points based on input parameters
     */
    function getPlotTrawlHaulChars(j_cycleStartDate,j_cycleEndDate) {	
		var get_stmt = api_base_uri+'/api/v1/source/trawl.operation_haul_fact/selection.csv?variables=date_dim$yyyymmdd,sampling_start_time_dim$hh24miss,sampling_end_time_dim$hh24miss,operation_dim$project_name,operation_dim$vessel,operation_dim$pass,operation_dim$leg,operation_dim$operation_id,operation_dim$performance_result,haul_latitude_dim$latitude_in_degrees,haul_longitude_dim$longitude_in_degrees,vessel_start_lat_dd,vessel_start_lon_dd,vessel_end_lat_dd,vessel_end_lon_dd,gear_start_lat_dd,gear_start_lon_dd,gear_end_lat_dd,gear_end_lon_dd,area_swept_ha_der,net_height_m_der,net_width_m_der,door_width_m_der,temperature_at_gear_c_der,temperature_at_surface_c_der,seafloor_depth_m_der,turbidity_ntu_der,salinity_at_gear_psu_der,o2_at_gear_ml_per_l_der,vertebrate_weight_kg,invertebrate_weight_kg,nonspecific_organics_weight_kg,fluorescence_at_surface_mg_per_m3_der';

		if( haulCharDataSourceStartDt==j_cycleStartDate && haulCharDataSourceEndDt==j_cycleEndDate )
		{
			showHidePrimitives(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key,null,true);
		
			trawlHaulCharsDataTable.rows.add( trawlHaulCharsDataTableArray ).nodes().to$().addClass( FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key );
			trawlHaulCharsDataTable.draw();

		}
		else
		{

			showHidePrimitives(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key,null,false);
			trawlHaulCharsDataTableArray = [];
			trawlHaulCharsDataTable.clear();

			//store the dates so if a user checks/unchecks
			//the Trawl Haul Chars layer, we don't have to 
			//make an API call as layer is not species specific
			haulCharDataSourceStartDt = j_cycleStartDate;
			haulCharDataSourceEndDt = j_cycleEndDate;

			$http.get(get_stmt,{ timeout: trawlHaulCharsCanceler.promise, params: {filters:'date_dim$yyyymmdd>='+j_cycleStartDate+',date_dim$yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{
				
				var jsonArray = CSV2JSON(csv);
				csv = null;
				var data = JSON.parse( jsonArray );

				if(data[data.length-1].operation_dim$operation_id===undefined)
					data.pop();

				if(!layerToPrimitiveIndexDict.has(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key))
					layerToPrimitiveIndexDict.set(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key, new Dict() );

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key, new Dict() );


				var el;
				var i=0;

				//Trawl Haul Chars will use the same layer to primitive hashmap
				//but instead of having the 2nd hashmap key off species, we just passing in a dummy string
				//where the dummy string = FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key
				layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).set(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key , new Cesium.PointPrimitiveCollection());

				while (el = data.shift()) {


					setRandomMapColor(el.operation_dim$vessel);

					trawlHaulCharsDataTableArray.push({"data":el,"rowId":i});

					layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).add({
						id: {
							layer: FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key,
							vessel:el.operation_dim$vessel,
							index: i
						},
						position : Cesium.Cartesian3.fromDegrees(el.haul_longitude_dim$longitude_in_degrees, el.haul_latitude_dim$latitude_in_degrees),
						color : randomColor.get(el.operation_dim$vessel),
						pixelSize : 10
					});


					i++;


	
				}; //end while loop

				scene.primitives.add( layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).get( FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key )   );
				layerToPrimitiveIndexDict.get(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key).set(FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key,scene.primitives.length-1);
				trawlHaulCharsDataTable.rows.add( trawlHaulCharsDataTableArray ).nodes().to$().addClass( FANCYTREE_ITEMS.TRAWL.HAUL_CHARS.key );
				autoResizeDatatable(trawlHaulCharsDataTable, 1);
				trawlHaulCharsDataTable.draw();

			}); //end $http.get	
		}// end else 
	}





    /**
     * Get hook and line specimens data from DB and plot points based on input parameters
     */
    function getPlotHookLineSpecimens(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/hooknline.individual_hooknline_view/selection.csv?variables=operation_dim$project_name,operation_dim$leg,date_dim$full_date,drop_time_dim$hh24miss,best_available_taxonomy_dim$scientific_name,best_available_taxonomy_dim$common_name,operation_dim$vessel,site_dim$area_name,site_dim$site_number,drop_latitude_dim$latitude_in_degrees,drop_longitude_dim$longitude_in_degrees,drop_sounder_depth_dim$depth_meters,hook_dim$hook_number,hook_dim$hook_result,sex_dim$sex,length_cm,age_years,weight_kg,otolith_number,fin_clip_number,operation_dim$operation_number,project_cycle';
		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, self.checkedLayers) >= 0)
			 showSpecies= true;

		var existingHookLineSpecimenData;
		var newSpecies = [];
		
		for(var i=0;i<j_species_codes.length;i++)
		{
			existingHookLineSpecimenData = showHidePrimitives(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key,j_species_codes[i],showSpecies);
			
			if (existingHookLineSpecimenData)
			{
				if (showSpecies)
					hookLineSpecimensDataTable.rows.add(hookLineSpecimensDataTableDict.get(j_species_codes[i].replace(/\s+/g, ''))).draw().nodes().to$().addClass(j_species_codes[i].toString().replace(/\s+/g, '') );
			}
			else
				newSpecies.push(j_species_codes[i]);
		}


		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{

			$http.get(get_stmt,{timeout: hookLineSpecimenCanceler.promise, params: {best_available_taxonomy_dim$scientific_name:newSpecies,filters:'date_dim$yyyymmdd>='+j_cycleStartDate+',date_dim$yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{

	
				var newHookLineSpecimenDataSources = new Dict();
				var newHookLineSpecimenDataSource;

				var jsonArray = CSV2JSON(csv);
				csv = null;
				var data = JSON.parse( jsonArray );

				if(data[data.length-1].best_available_taxonomy_dim$scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveIndexDict.has(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key))
					layerToPrimitiveIndexDict.set(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, new Dict() );

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key, new Dict() );

				var el;
				var i=0;
				while (el = data.shift()) {
					var newSpeciesNoBlanks = (el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '');


					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).has( newSpeciesNoBlanks ) )
					{
							layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).set(newSpeciesNoBlanks , new Cesium.PointPrimitiveCollection());
							hookLineSpecimensDataTableDict.set (newSpeciesNoBlanks , [] );
					}
					

					hookLineSpecimensDataTableDict.get( newSpeciesNoBlanks ).push({"data":el, "rowId":newSpeciesNoBlanks+i});
		
					setRandomMapColor(newSpeciesNoBlanks);
						


					if( el.weight_kg>0 )
					{
						layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).get(newSpeciesNoBlanks).add({
							id: {
								layer: FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key,
								scientificName: el.best_available_taxonomy_dim$scientific_name,
								index: i
							},
							position : Cesium.Cartesian3.fromDegrees(el.drop_longitude_dim$longitude_in_degrees, el.drop_latitude_dim$latitude_in_degrees),
							color : randomColor.get(newSpeciesNoBlanks),
							pixelSize : 10
						});
					}
					
					i++;



				}; //end for loop

				while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).has(newSpeciesNoBlanks))
					{
						scene.primitives.add( layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).get( newSpeciesNoBlanks )   );
						layerToPrimitiveIndexDict.get(FANCYTREE_ITEMS.HOOK_LINE.SPECIMENS.key).set(newSpeciesNoBlanks,scene.primitives.length-1);
					}

					if(hookLineSpecimensDataTableDict.has( newSpeciesNoBlanks ))
						hookLineSpecimensDataTable.rows.add(hookLineSpecimensDataTableDict.get( newSpeciesNoBlanks ) ).draw().nodes().to$().addClass( newSpeciesNoBlanks );
				}

				autoResizeDatatable(hookLineSpecimensDataTable, 3);


			}); //end $http.get

			
		} // end dataSourceExistsBySpecies else condition
    }








    /**
     * Get hook and line catch data from DB and plot points based on input parameters
     */
    function getPlotHookLineCatch(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/hooknline.catch_hooknline_view/selection.csv?variables=project_name,leg,date_dim$full_date,best_available_taxonomy_dim$scientific_name,best_available_taxonomy_dim$common_name,vessel,site_dim$site_latitude_dd,site_dim$site_longitude_dd,total_catch_numbers,total_catch_wt_kg,site_dim$area_name,site_dim$site_number,wave_height_m,swell_direction_mag,swell_height_m,sea_surface_temp_c,ctd_sounder_depth_m,ctd_on_bottom_measure_depth_dim$depth_meters,ctd_on_bottom_temp_c,ctd_on_bottom_salinity_psu,ctd_on_bottom_disolved_oxygen_sbe43_ml_per_l,ctd_on_bottom_disolved_oxygen_aanderaa_ml_per_l';

		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, self.checkedLayers) >= 0)
			 showSpecies= true;

		var existingHookLineCatchData;
		var newSpecies = [];
		
		for(var i=0;i<j_species_codes.length;i++)
		{
			existingHookLineCatchData = showHidePrimitives(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key,j_species_codes[i],showSpecies);
			
			if (existingHookLineCatchData)
			{
				if (showSpecies)
					hookLineCatchDataTable.rows.add(hookLineCatchDataTableDict.get(j_species_codes[i].replace(/\s+/g, ''))).draw().nodes().to$().addClass(j_species_codes[i].toString().replace(/\s+/g, '') );
			}
			else
				newSpecies.push(j_species_codes[i]);
		}

		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{

			$http.get(get_stmt,{timeout: hookLineCatchCanceler.promise, params: {best_available_taxonomy_dim$scientific_name:newSpecies,filters:'date_dim$yyyymmdd>='+j_cycleStartDate+',date_dim$yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{

	
				var newHookLineCatchDataSources = new Dict();
				var newHookLineCatchDataSource;

				var jsonArray = CSV2JSON(csv);
				csv = null;
				var data = JSON.parse( jsonArray );

				if(data[data.length-1].best_available_taxonomy_dim$scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveIndexDict.has(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key))
					layerToPrimitiveIndexDict.set(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, new Dict() );

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, new Dict() );

				var el;
				var i=0;
				while (el = data.shift()) {

					var newSpeciesNoBlanks = (el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '');

					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).has( newSpeciesNoBlanks ) )
					{
							layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).set(newSpeciesNoBlanks , new Cesium.PointPrimitiveCollection());
							hookLineCatchDataTableDict.set (newSpeciesNoBlanks , [] );
					}
						
			
					hookLineCatchDataTableDict.get( newSpeciesNoBlanks ).push({"data":el, "rowId":newSpeciesNoBlanks+i});
					setRandomMapColor(newSpeciesNoBlanks);

					if( el.total_catch_wt_kg>0 )
					{
						layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).get(newSpeciesNoBlanks).add({
							id: {
								layer: FANCYTREE_ITEMS.HOOK_LINE.CATCH.key,
								scientificName: el.best_available_taxonomy_dim$scientific_name,
								index: i
							},
							position : Cesium.Cartesian3.fromDegrees(el.site_dim$site_longitude_dd, el.site_dim$site_latitude_dd),
							color : randomColor.get(newSpeciesNoBlanks),
							pixelSize : 10
						});
					}
					
					i++;

				}; //end for loop

				while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).has(newSpeciesNoBlanks))
					{
						scene.primitives.add( layerToPrimitiveDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).get( newSpeciesNoBlanks )   );
						layerToPrimitiveIndexDict.get(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key).set(newSpeciesNoBlanks,scene.primitives.length-1);
					}

					if(hookLineCatchDataTableDict.has( newSpeciesNoBlanks ))
						hookLineCatchDataTable.rows.add(hookLineCatchDataTableDict.get( newSpeciesNoBlanks ) ).draw().nodes().to$().addClass( newSpeciesNoBlanks );
				}

				autoResizeDatatable(hookLineCatchDataTable, 4);


			}); //end $http.get

			
		} // end dataSourceExistsBySpecies else condition
    }





    /**
     * Get trawl catch species data from DB and plot points based on input parameters
     */
    function getPlotTrawlCatch(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/trawl.catch_fact/selection.csv?variables=date_dim$full_date,sampling_start_time_dim$hh24miss,sampling_end_time_dim$hh24miss,operation_dim$vessel,operation_dim$pass,operation_dim$leg,operation_dim$operation_id,haul_latitude_dim$latitude_in_degrees,haul_longitude_dim$longitude_in_degrees,target_station_design_dim$station_code,best_available_taxonomy_dim$scientific_name,subsample_wt_kg,subsample_count,total_catch_wt_kg,total_catch_numbers,taxonomy_observation_detail_dim$measurement_procurement,statistical_partition_dim$statistical_partition_value,operation_dim$performance_result,seafloor_depth_dim$depth_meters,cpue_kg_per_ha_der,target_station_design_dim$date_stn_invalid_for_trawl_whid,statistical_partition_dim$statistical_partition_value,field_identified_taxonomy_dim$scientific_name,best_available_taxonomy_dim$common_name,operation_dim$project_name';

		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.TRAWL.CATCH.key, self.checkedLayers) >= 0)
			showSpecies = true;

		var existingTrawlCatchData;
		var newSpecies = [];
		
		for(var i=0;i<j_species_codes.length;i++)
		{
			existingTrawlCatchData = showHidePrimitives(FANCYTREE_ITEMS.TRAWL.CATCH.key,j_species_codes[i],showSpecies);
			
			if (existingTrawlCatchData)
			{
				if (showSpecies)
					trawlCatchDataTable.rows.add(trawlCatchDataTableDict.get(j_species_codes[i].replace(/\s+/g, ''))).draw().nodes().to$().addClass(j_species_codes[i].toString().replace(/\s+/g, '') );
			}
			else
				newSpecies.push(j_species_codes[i]);
		}

//		console.log(' newSpecies='+newSpecies);
		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{
			$http.get(get_stmt,{timeout: trawlCatchCanceler.promise, params: {best_available_taxonomy_dim$scientific_name:newSpecies,filters:'date_dim$yyyymmdd>='+j_cycleStartDate+',date_dim$yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{
		
				var jsonArray = CSV2JSON(csv);
				csv = null;

				var data = JSON.parse( jsonArray );

				if(data[data.length-1].best_available_taxonomy_dim$scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveIndexDict.has(FANCYTREE_ITEMS.TRAWL.CATCH.key))
					layerToPrimitiveIndexDict.set(FANCYTREE_ITEMS.TRAWL.CATCH.key, new Dict() );

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.TRAWL.CATCH.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.TRAWL.CATCH.key, new Dict() );


				var el;
				var i=0;

				while (el = data.shift()) {

					var newSpeciesNoBlanks = (el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '');


					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).has( newSpeciesNoBlanks ) )
					{
							layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).set(newSpeciesNoBlanks , new Cesium.PointPrimitiveCollection());
							trawlCatchDataTableDict.set (newSpeciesNoBlanks , [] );
					}
					

					trawlCatchDataTableDict.get( (el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '')).push({"data":el, "rowId":(el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '')+i});
		
					setRandomMapColor(el.best_available_taxonomy_dim$scientific_name);

					if( el.total_catch_wt_kg>0 )
					{
						layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).get(newSpeciesNoBlanks).add({
							id: {
								layer: FANCYTREE_ITEMS.TRAWL.CATCH.key,
								scientificName: el.best_available_taxonomy_dim$scientific_name,
								index: i
							},
							position : Cesium.Cartesian3.fromDegrees(el.haul_longitude_dim$longitude_in_degrees, el.haul_latitude_dim$latitude_in_degrees),
							color : randomColor.get(el.best_available_taxonomy_dim$scientific_name),
							pixelSize : 10
						});
					}

					i++;


				}; //end for loop


				while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).has(newSpeciesNoBlanks))
					{
						scene.primitives.add( layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).get( newSpeciesNoBlanks )   );
						layerToPrimitiveIndexDict.get(FANCYTREE_ITEMS.TRAWL.CATCH.key).set(newSpeciesNoBlanks,scene.primitives.length-1);
					}

					if(trawlCatchDataTableDict.has( newSpeciesNoBlanks ))
						trawlCatchDataTable.rows.add(trawlCatchDataTableDict.get( newSpeciesNoBlanks ) ).draw().nodes().to$().addClass( newSpeciesNoBlanks );
				}

				autoResizeDatatable(trawlCatchDataTable, 2);

			}); //end $http.get
		} // end dataSourceExistsBySpecies else condition
    }








    /**
     * Get species data from DB and plot points based on input parameters
     */
    function getPlotTrawlSpecimens(j_species_codes,j_cycleStartDate,j_cycleEndDate) {


		var individualOrganismsTableData = [];

		var get_stmt = api_base_uri+'/api/v1/source/trawl.individual_fact/selection.csv?variables=date_dim$yyyymmdd,sampling_start_time_dim$hh24miss,sampling_end_time_dim$hh24miss,operation_dim$vessel,operation_dim$pass,operation_dim$leg,operation_dim$operation_id,field_identified_taxonomy_dim$scientific_name,best_available_taxonomy_dim$scientific_name,best_available_taxonomy_dim$common_name,haul_latitude_dim$latitude_in_degrees,haul_longitude_dim$longitude_in_degrees,target_station_design_dim$station_code,sex_dim$sex,length_cm,age_years,weight_kg,seafloor_depth_dim$depth_meters,operation_dim$project_name';

		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, self.checkedLayers) >= 0)
			showSpecies = true;

		var existingSpeciesData = false;
		var newSpecies = [];




		

		for(var i=0;i<j_species_codes.length;i++)
		{
			existingSpeciesData = showHidePrimitives(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key,j_species_codes[i],showSpecies);
			
			if (existingSpeciesData)
			{
				if (showSpecies)
					trawlSpecimensDataTable.rows.add(trawlSpecimensDataTableDict.get(j_species_codes[i].replace(/\s+/g, ''))).draw().nodes().to$().addClass(j_species_codes[i].toString().replace(/\s+/g, '') );
			}
			else
				newSpecies.push(j_species_codes[i]);
		}








		//console.log(' newSpecies='+newSpecies);
		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{

				//					console.log("key toString"+newTrawlCatchDataSources.keys[i].toString().replace(/\s+/g, ''));
			$http.get(get_stmt,{timeout: trawlSpecimensCanceler.promise, params: {best_available_taxonomy_dim$scientific_name:newSpecies,filters:'date_dim$yyyymmdd>='+j_cycleStartDate+',date_dim$yyyymmdd<='+j_cycleEndDate}}).success(function(csv)
			{
				
				var jsonArray = CSV2JSON(csv);
				csv = null;

				var data = JSON.parse( jsonArray );

				if(data[data.length-1].best_available_taxonomy_dim$scientific_name===undefined)
					data.pop();

				if(!layerToPrimitiveIndexDict.has(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key))
					layerToPrimitiveIndexDict.set(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, new Dict() );

				if(!layerToPrimitiveDict.has(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key))
					layerToPrimitiveDict.set(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key, new Dict() );


				var el;
				var i=0;

				while (el = data.shift()) {

					var newSpeciesNoBlanks = (el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '');


					if ( !layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).has( newSpeciesNoBlanks ) )
					{
							layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).set(newSpeciesNoBlanks , new Cesium.PointPrimitiveCollection());
							trawlSpecimensDataTableDict.set (newSpeciesNoBlanks , [] );
					}
					

					trawlSpecimensDataTableDict.get( (el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '')).push({"data":el, "rowId":(el.best_available_taxonomy_dim$scientific_name).replace(/\s+/g, '')+i});

					setRandomMapColor(el.best_available_taxonomy_dim$scientific_name);


					layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).get(newSpeciesNoBlanks).add({
						id: {
							layer: FANCYTREE_ITEMS.TRAWL.SPECIMENS.key,
							scientificName: el.best_available_taxonomy_dim$scientific_name,
							index: i
						},
						position : Cesium.Cartesian3.fromDegrees(el.haul_longitude_dim$longitude_in_degrees, el.haul_latitude_dim$latitude_in_degrees),
						color : randomColor.get(el.best_available_taxonomy_dim$scientific_name),
						pixelSize : 10
					});


					i++;
				}; //end for loop

				
				

				
				while (el = newSpecies.shift()) {
					var newSpeciesNoBlanks = (el).replace(/\s+/g, '');

					if(layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).has(newSpeciesNoBlanks))
					{
						scene.primitives.add( layerToPrimitiveDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).get( newSpeciesNoBlanks )   );
						layerToPrimitiveIndexDict.get(FANCYTREE_ITEMS.TRAWL.SPECIMENS.key).set(newSpeciesNoBlanks,scene.primitives.length-1);
					}



					if(trawlSpecimensDataTableDict.has( newSpeciesNoBlanks ))
					{
						
				

						trawlSpecimensDataTable.rows.add(trawlSpecimensDataTableDict.get( newSpeciesNoBlanks ) ).draw().nodes().to$().addClass( newSpeciesNoBlanks );
					
					}
				}


				autoResizeDatatable(trawlSpecimensDataTable, 0);

			}); //end $http.get
		} // end dataSourceExistsBySpecies else condition



    }




    /**
     * Get Observer Catch data from DB and add them to the datatables (no need to plot as there are no lat/longs)
     */
    function getObserverCatch(j_species_codes,j_cycleStartDate,j_cycleEndDate) {

		var get_stmt = api_base_uri+'/api/v1/source/observer.catch_observer_view/selection.csv?variables=taxonomy_dim$scientific_name,taxonomy_dim$common_name,season_year,report_category,catch_updated_date,discard_weight_est_lbs,discard_count_est';

		var start_season_year = j_cycleStartDate.substring(0, 4);
		var end_season_year = j_cycleEndDate.substring(0, 4);


		var showSpecies = false;
		if ($.inArray(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key, self.checkedLayers) >= 0)
			 showSpecies= true;

		var existingObserverCatchData = null;
		var newSpecies = [];
		

		for(var i=0;i<j_species_codes.length;i++)
		{

			existingObserverCatchData = observerCatchDataTableDict.get( (j_species_codes[i]).replace(/\s+/g, '') );
			
			if (existingObserverCatchData)
			{
				console.log('Found existing observer catch info for species = '+(j_species_codes[i]).replace(/\s+/g, ''));
				
				if (showSpecies)
				{
					console.log('Show existing observer catch info ');
					observerCatchDataTable.rows.add(existingObserverCatchData).draw().nodes().to$().addClass(j_species_codes[i].toString().replace(/\s+/g, '') );
	
				}


			}
			else
				newSpecies.push(j_species_codes[i]);
		}


		if (newSpecies != null && newSpecies.length>0 && showSpecies)
		{
			$http.get(get_stmt,{timeout: observerCatchCanceler.promise, params: {taxonomy_dim$scientific_name:newSpecies,filters:'season_year>='+start_season_year+',season_year<='+end_season_year}}).success(function(csv)
			{

				var jsonArray = CSV2JSON(csv);
				csv = null;
				var data = JSON.parse( jsonArray );

				if(data[data.length-1].taxonomy_dim$scientific_name===undefined)
					data.pop();


				var el;
				var i=0;
				var newObserverCatchDataTableDict = new Dict();

				while (el = data.shift()) {

						
					var newSpeciesNoBlanks = (el.taxonomy_dim$scientific_name).replace(/\s+/g, '');

					if ( !newObserverCatchDataTableDict.get( newSpeciesNoBlanks ) )
						 newObserverCatchDataTableDict.set (newSpeciesNoBlanks, [] );

					newObserverCatchDataTableDict.get( newSpeciesNoBlanks ).push({"data":el, "rowId":newSpeciesNoBlanks+i});


				}; //end for loop

				for (var i = 0; i < newObserverCatchDataTableDict.values.length; i++) {

					observerCatchDataTableDict.set( newObserverCatchDataTableDict.keys[i] , newObserverCatchDataTableDict.values[i] );
					observerCatchDataTable.rows.add(newObserverCatchDataTableDict.get( newObserverCatchDataTableDict.keys[i] ) ).draw().nodes().to$().addClass( newObserverCatchDataTableDict.keys[i].toString() );
				}

				autoResizeDatatable(observerCatchDataTable, 5);


			}); //end $http.get

			
		} // end dataSourceExistsBySpecies else condition
  
	}




   /**
     * Auto resizes datatable based on row count
	 * Input: datatable and tableIndex (the order of the tables in view1.html)
     */
    function autoResizeDatatable(datatable, tableIndex) {

		var minRowHeight = 52;
		var rowHeight = 35;
		var maxRows = Math.floor(datatableScrollerHeight / rowHeight)-2;
		
		if(datatable.rows().count()<2)
			$('div.dataTables_scrollBody').eq( tableIndex ).height(minRowHeight+'px');
		else if(datatable.rows().count()<maxRows)
			$('div.dataTables_scrollBody').eq( tableIndex ).height( (datatable.rows().count()-1)*rowHeight+minRowHeight+'px');
		else
			$('div.dataTables_scrollBody').eq( tableIndex ).height( datatableScrollerHeight+'px');


	}

   /**
     * Takes a key (scientific name, vessel) input and sets a random Cesium map 
	 * color for that ID. The first 10 colors are pre-selected to be bright.
     */
    function setRandomMapColor(key) {
		if (randomColor.get(key) == null)
		{
			if (topTenCesiumColorCounter<10)
			{
				randomColor.set(key,topTenCesiumColorArray[topTenCesiumColorCounter] );
				topTenCesiumColorCounter++;
			}
			else
			{
				randomColor.set(key,Cesium.Color.fromRandom({
					alpha : 1.0,
					minimumRed : 0.5,
					minimumGreen : 0.5,
					minimumBlue : 0.5
				}) );
			}
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
		.domain([new Date('01/01/1998'), 
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


});


/*********************************************************************************************************************************************
	Function to be called when time filter is updated
**********************************************************************************************************************************************/
	function brushed() {


		//remove any selected point that the user might have clicked on the map
		viewer.entities.removeAll();

		//remove all point primitives from the map
		scene.primitives.removeAll();

		//clear all datatable hashmaps containing the datatable array of objects
		trawlSpecimensDataTableDict.clear();
		trawlCatchDataTableDict.clear();
		hookLineSpecimensDataTableDict.clear();
		hookLineCatchDataTableDict.clear();
		observerCatchDataTableDict.clear();

		//clear all datatables
		trawlSpecimensDataTable.clear().draw();
		trawlHaulCharsDataTable.clear().draw();
		trawlCatchDataTable.clear().draw();
		hookLineSpecimensDataTable.clear().draw();
		hookLineCatchDataTable.clear().draw();
		observerCatchDataTable.clear().draw();
		
		layerToPrimitiveIndexDict.clear();
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
		{	

			hookLineSpecimensMapCount = 0;
			hookLineSpecimensTotalCount = 0;
			getPlotHookLineSpecimens(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);
		}
			 
		if ($.inArray(FANCYTREE_ITEMS.HOOK_LINE.CATCH.key, list) >= 0)
			getPlotHookLineCatch(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);

		if ($.inArray(FANCYTREE_ITEMS.OBSERVER.CATCH_EXPANSIONS.key, list) >= 0)
			getObserverCatch(j_species_codes,startDateyyyymmdd,endDateyyyymmdd);


		

		
		}


	//populate years, for the time filtere
	var timefilter_start_year = 1998 //start the time player from year 1998
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

    // now draw the brush to match our extent
    // use transition to slow it down so we can see what is happening
    // remove transition so just d3.select(".brush") to just draw
    brush(d3.select(".brush").transition());

    // now fire the brushstart, brushmove, and brushend events
    // remove transition so just d3.select(".brush") to just draw
    brush.event(d3.select(".brush").transition().delay(1000))


}]) //end View1Ctrl 