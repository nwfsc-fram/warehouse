# FRAM Data Warehouse web service - Test Plan

2016-FEB-05

Testing plan to be conducted before public release of *FRAM Data Warehouse web service* code updates.

## Test Plan prerequisites

1. __Code verification results__ - Results of the code review conducted for this release (Includes SHA256 checksum of the reviewed package).
2. __Testing server__ - A web server, on to which the candidate package has been installed per Product Installation steps.
3. __Testing database__ - An EnterpriseDB Postgres Advanced Database instance loaded with Data Warehouse schema (e.g.: dw, dwsupport) and a known quantity of FRAM project datasets.
3. __Tester workstation__ - A PC for use in completing the test plan.

### Testing database - datasets required
TBD

### Tester workstation - required software
* __ab (Apache bench)__ - Tester pc can be configured with required software by:
  1. cloning git repository
  2. running *make && package && deploy_install* per product Build documentation
  3. installation of CentOS *httpd-tools* package


## Test Plan

1. __Configure Testing server with artificial memory limit.__ Use below commands to temporarily recreate an availability issue, by placing a hard (a)ddress (s)pace limit on service processes:

```bash
$ sudo service httpd stop
$ echo 'apache hard    as  1109500' | sudo tee > /etc/security/limits.d/98-apache-TEST.conf
$ sudo service httpd start
```

2. __Simulate load with Tester workstation.__ 
  1. Use below command to begin requesting data from the service (Substitute $MY_TEST_SERVER with Test server host address):

```bash
$  ab -c 1 'https://$MY_TEST_SERVER:8080/data/api/v1/source/warehouse/selection.json?filters=trawl.SpeciesResource$species_code=50,trawl.LenAgeWMat$capture_date>07/01/2014,trawl.LenAgeWMat$species_code=30240,trawl.MockRollupByDayHaulCharsSat$capture_date=2014-09-16T00:00:00Z,trawl.HaulCharsSat$haul_identifier=201403010142,observer.SalmonReport$wcgop_species_updated_date~=(2015),trawl.SpeciesCatchSat$scientific_name=shark%20unident.,taxonomy_dim$common_name=shark%20unident.,depth_dim$depth_meters=444.2'
```

  2. After more than one error has accumulated (approximately: 2 minutes, or 400+ requests) press Ctrl-C to halt testing.
  3. Record the status code indicating service is still available, as returned by the first line of command:
    * __Status:__ ____________________________
    * __Status (expected):__ 'HTTP/1.1 200 OK'

```bash
$ curl --insecure --head --request GET 'https://$MY_TEST_SERVER:8080/data/api/v1/source/warehouse/selection.json?filters=trawl.SpeciesResource$species_code=50,trawl.LenAgeWMat$capture_date>07/01/2014,trawl.LenAgeWMat$species_code=30240,trawl.MockRollupByDayHaulCharsSat$capture_date=2014-09-16T00:00:00Z,trawl.HaulCharsSat$haul_identifier=201403010142,observer.SalmonReport$wcgop_species_updated_date~=(2015),trawl.SpeciesCatchSat$scientific_name=shark%20unident.,taxonomy_dim$common_name=shark%20unident.,depth_dim$depth_meters=444.2'
```

3. __Remove artificial limit from Testing server.__ Use below commands to remove the availability issue:

```bash
$ sudo service httpd stop
$ sudo rm -f /etc/security/limits.d/98-apache-TEST.conf
$ sudo service httpd start
```

