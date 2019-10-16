import qs from 'qs';
import Axios from 'axios';

export async function authenticate(): Promise<Object> {
    /**
     * Function to retrieve an authentication token frome the Data Warehouse
     * API. This token can then be used in future AXIOS queries.
     */
    let authUrl = 'https://www.nwfsc.noaa.gov/data/api/v1/external/login'
    let data = qs.stringify({
        "username": "nmfs.nwfsc.fram.data.team+pacfin@noaa.gov",
        "password": "S3ct0rdef$1234"
    });
    const response = await Axios.post(authUrl, data, {
        headers: {'Content-Type' : 'application/x-www-form-urlencoded',
        }
    });
    return response.data;
}

async function exampleExternalUserDataPull(startYear: string, endYear: string)  {
    /**
     * This barebones function is a test data pull showing how to use an authorization token
     * to run a query to the data warehouse. Notice in particular the additional header value
     * in the Axios query that contains the authToken
     */

    // Retrieve Trawl Survey Haul Characteristics data from FRAM Data Warehouse
    let baseUrl = "https://www.nwfsc.noaa.gov/data/api/v1/source/trawl.operation_haul_fact/selection.";
    let selectionType = "csv";  // You can also chose to return the query results as json with "json"
    let variables = "latitude_hi_prec_dd,longitude_hi_prec_dd,tow_end_timestamp,tow_start_timestamp,trawl_id,vessel,sampling_start_hhmmss,sampling_end_hhmmss";
    let filters = "year>=" + startYear + ",year<=" + endYear + ",vessel=Coast Pride";
    // String together query parameters with ampersands
    let dwUrl = baseUrl + selectionType + "?" + "filters=" + filters + "&" + "variables=" + variables;

    // This example only pulls the data down, you can also save out the data object to a file
    // if desired
    try {
        let authToken = await authenticate();
        let data: any;

        const response = await Axios.get(dwUrl, {
            headers: {
                "Accept": "application/json",
                "authorization": authToken
            }
        });
        data = response.data;
        console.log(`data retrieved successfully`);
        // print data to screen so you can see the default output formatting for csv option
        console.log(data);
    } catch (e) {
        console.log(`Error in retrieving trawl survey haul data: ${e}`);
    }
}

async function runner() {
    let hauls = await exampleExternalUserDataPull('2000', '2001');
}

runner();



// Copy of the package.json for this script
`
{
    "name": "test",
    "version": "1.0.0",
    "description": "",
    "main": "index.js",
    "dependencies": {
      "@types/node": "^12.7.12",
      "@types/qs": "^6.5.3",
      "axios": "^0.19.0",
      "qs": "^6.9.0",
      "typescript": "^3.6.4"
    },
    "devDependencies": {},
    "scripts": {
      "test": "echo \"Error: no test specified\" && exit 1"
    },
    "author": "",
    "license": "ISC"
  }

`