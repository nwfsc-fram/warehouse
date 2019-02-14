#!/usr/bin/env python

from setuptools import setup, find_packages

requires = [
    'waitress(<1.1)',
    'falcon(<=0.3)',
    'werkzeug(<0.13)',
    'sqlalchemy(>=1.1, <1.2)',
    'psycopg2(<2.8)',
    'simplejson(<4)',
    'python-dateutil(==2.4.2)',
    'numpy(<1.13)',
    'pandas(==0.18.1)',
    'pyparsing(<2.3)',
    'pycrypto(==2.7a1)',
    'lxml(==3.6.1)',
    'pygeometa(>=0.2.2)',
    'pycsw(==2.0.0a1)',
    'filelock(<2.1)',
    'ldap3(<2.3)',
    'beaker(>=1.9, <2.0)',
    'grip(>=4.0, <5.0)',
    'requests(<2.18)',
    'python3-saml(>=1.2.6, <1.3)
]

dependency_links = [
    'git+https://github.com/bjamesv/dateutil.git@9193f62#egg=python-dateutil-2.4.2',
    'git+https://github.com/dlitz/pycrypto.git@7acba5f#egg=pycrypto-2.7a1'
]

test_requirements = ['pylint(>=1.7.1, <2.0)']

setup(name='Warehouse API',
      version='1.4',
      description='Data Warehouse API wsgi application',
      author='NOAA NMFS/NWFSC FRAM',
      author_email='nmfs.nwfsc.fram.data.team@noaa.gov',
      url='https://github.com/nwfsc-fram/warehouse',
      packages=find_packages(),
      install_requires=requires,
      dependency_links=dependency_links,
      tests_require=test_requirements
     )
