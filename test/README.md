# Functional tests

FRAM Data Warehouse functional tests.

# Running
To run the Warehouse server functional testing suite:
1. Obtain location details of the Warehouse instance to be tested & update _test/test.ini_ with the instance:
  * hostname
  * port
  * URL scheme

2. pip install -r test/requirements.txt

 (Optionally) create a Python virtualenv, to contain test suite requirements:
 ```bash
virtualenv -p python3 test/environment-test
source test/environment-test/bin/activate
pip install -r test/requirements.txt
 ```

3. 
 ```bash
cd test/
python3 -m unittest discover
 ```

4. If Python virtualenv was created in step 2., deactivate it to finish test execution.
 ```bash
deactivate
 ```
