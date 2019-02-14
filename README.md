# FRAM Data Warehouse - Public

Public code for the FRAM data warehouse. Project is organized as follows:

- [server](#server)
	- [api](#api) - RESTful application programming interface into the data warehouse
	- [app](server/app/) - client-side AngularJS application
- [test](#test) - Python _unittest_ functional test suite

## Database
For instructions on creating/configuring the data warehouse DB see private project [warehouse-internal](<mailto:nmfs.nwfsc.fram.data.team@noaa.gov?subject=warehouse-internal git repository>).

## Server
A Makefile has been provided in the [server/](server/) project folder, to facilitate automated building of Python virtualenv and running the server. Virtualenv is constructed with the help of Continuum Analytics "Anaconda" Python distribution.

*Powered by [Anaconda](http://docs.continuum.io/anaconda/eula.html)*
### Prerequisites
Makefile can be run on any system with:
  * _wget, make, bash, & tar_ (I used Debian Wheezy)
  * postgresql-devel tools package
  * libxml2-devel package
  * libxslt-devel package
  * xmlsec1-devel xmlsec1-openssl-devel libtool-ltdl-devel packages (per: [xmlsec](http://pythonhosted.org/xmlsec/install.html#linux-centos))
  * java 8 (e.g.: openjdk-8-jre package)

Makefile target _pretest_ requires additional commands:
  * _curl, zip_

### Usage
1. Data source db backend connections must be configured via:
  * _server/db_config.ini_
     * see [Production Installation, step #2.7.1](deployment.md#api) for details
  * (Optional) The server port/interface may be configured via:
     * _server/server.ini_

2. Obtain needed modules via included _server/requirements.txt_
 ```bash
pip install --no-binary lxml,xmlsec -r build/server/requirements.txt
 ```

 (Optional) Using Continuum Analytics Anaconda, a Python virtualenv may be constructed via Makefile default target (default target name: _build_).
 ```bash
cd server/
make
 ```
 (Optional) Anacondas virtualenv will be constructed in _server/build/_. Virtualenv may be enabled and disabled via:
 ```bash
source build/miniconda3/bin/activate warehouse-env
source deactivate
 ```

3. Run Python test cases via:
 ```bash
cd server/
python3 -m unittest discover
 ```
 (Optional) Test cases may be started via the virtualenv with:
 ```bash
cd server/
make && make test
make test # retest, if virtualenv has already been built/requirements.txt unchanged
 ```

4. Start the Warehouse HTTP server via:
 ```bash
cd server/
python3 server.py
 ```
 (Optional) Server may be launched via virtualenv with:
 ```bash
cd server/
make && make run
make run # rerun, if virtualenv has already been built/requirements.txt unchanged
 ```

#### Jenkins
See [warehouse-internal](<mailto:nmfs.nwfsc.fram.data.team@noaa.gov?subject=warehouse-internal git repository>) for job config settings & instructions on setup/installation of new Jenkins build jobs.

### API
See: [Client API documentation](server/doc/Client API.md).

### Packaging
The service may be packaged for distribution/production installation via the Makefile _package_ target:
```bash
cd server/
make && make package
```

### Production Installation
Process for installing Warehouse service package on a CentOS 6 host:

See: [deployment.md](deployment.md)

### Running
The installed Warehouse server may be managed via Apache service: _httpd_.
```bash
sudo service httpd start
sudo service httpd stop
sudo service httpd status
```

Warehouse application will not begin running, until a page request for any API URL is made. This means the Pentaho ETL-scheduler subprocess will not start until after a URL request is made. The CSW subservice will not start until 6 minutes after the first URL request is made (after startup, PyCSW will periodically refresh its metadata cache every additional 6 minutes).

### LDAP Certificates
When NOAA incrementally updates LDAP server certificates, place the new issuing CA Root certificate in: [server/api/auth/noaa-ldap-certs.crt](server/api/auth/noaa-ldap-certs.crt)

The warehouse .crt file may contain mulitple Root certificates, to support environments where a mix of certificates are being used concurrently & for seamless transition from the old certificates to the new certificates.

Remove all old certs from warehouse .crt file when server certificates have been fully decommissioned.

If the CA chain certs needed to verify LDAP server identity cannot be found, `Service Unavailable` will be displayed to the user and warehouse will log:
```
WARNING:root:(LDAPSocketOpenError('socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:600)',),)
WARNING:root:('unable to open socket', [(datetime.datetime(2017, 6, 13, 11, 1, 38, 39227), <class 'ldap3.core.exceptions.LDAPSocketOpenError'>, LDAPSocketOpenError('socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:600)',), ('**EDIT:SERVER_IP1**', 636)), (datetime.datetime(2017, 6, 13, 11, 1, 38, 195164), <class 'ldap3.core.exceptions.LDAPSocketOpenError'>, LDAPSocketOpenError('socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:600)',), ('**EDIT:SERVER_IP1**', 636))])
WARNING:root:('unable to open socket', [(datetime.datetime(2017, 6, 13, 11, 1, 38, 427809), <class 'ldap3.core.exceptions.LDAPSocketOpenError'>, LDAPSocketOpenError('socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:600)',), ('**EDIT:SERVER_IP1**', 636)), (datetime.datetime(2017, 6, 13, 11, 1, 38, 634087), <class 'ldap3.core.exceptions.LDAPSocketOpenError'>, LDAPSocketOpenError('socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:600)',), ('**EDIT:SERVER_IP2**', 636)), (datetime.datetime(2017, 6, 13, 11, 1, 38, 842860), <class 'ldap3.core.exceptions.LDAPSocketOpenError'>, LDAPSocketOpenError('socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:600)',), ('**EDIT:SERVER_IP3**', 636))])
```

### Updating
1. The installed Warehouse server may be updated with a new application package via:
   1. Specify currently installed version

            read -p "Enter backup ID [e.g.: '1.1']: " WH_BACKUP_ID && CURRENT_WH_VER=${WH_BACKUP_ID}_$(date -I'minutes')

   2. Back up installed Warehouse (*DO NOT SKIP*) & install new Warehouse scripts

            mkdir -p /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}
            mv -f /var/www/wsgi-scripts/warehouse/server /var/www/wsgi-scripts/warehouse/miniconda3 /var/www/wsgi-scripts/warehouse/Miniconda3-*-Linux-x86_64.sh /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/.
            # Untar install package
            tar xzf /path/to/warehouse-server.tgz --directory=/var/www/wsgi-scripts/warehouse
            # Reinstall Continuum Analytics Anaconda
            #  back up package environment and clear Anaconda dir
            mv /var/www/wsgi-scripts/warehouse/miniconda3/envs /var/www/wsgi-scripts/warehouse/.
            rm -Rf /var/www/wsgi-scripts/warehouse/miniconda3
            #  run installer
            /var/www/wsgi-scripts/warehouse/Miniconda3-*-Linux-x86_64.sh -b -p /var/www/wsgi-scripts/warehouse/miniconda3
            #  replace package environment
            mv -f /var/www/wsgi-scripts/warehouse/envs /var/www/wsgi-scripts/warehouse/miniconda3/.
            #  restore web group ownership
            chown -R :webdev_warehouse /var/www/wsgi-scripts/warehouse/*
            chmod -R o+rx /var/www/wsgi-scripts/warehouse/*
            #  rebuild CentOS6 system library cache
            sudo ldconfig

   2. Restore saved Warehouse configuration
      * cp -f /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/server/server.ini /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/server/db_config.ini /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/server/db_dwsensitive.ini /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/server/db_dwsupport.ini /var/www/wsgi-scripts/warehouse/server/.
      * UMASK_PREV=$(umask) && rm -f /var/www/wsgi-scripts/warehouse/server/openssl-keystore.jks; umask 0207 && cp -f /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/server/openssl-keystore.jks /var/www/wsgi-scripts/warehouse/server/. && umask ${UMASK_PREV} && chown apache:webdev_warehouse /var/www/wsgi-scripts/warehouse/server/openssl-keystore.jks
      * UMASK_PREV=$(umask) && umask 077 && mkdir -p /var/www/wsgi-scripts/warehouse/server/api/auth/secrets && umask 0277 && cp -f /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/server/api/auth/secrets/saml-sp.key /var/www/wsgi-scripts/warehouse/server/api/auth/secrets/saml-sp.key && umask $UMASK_PREV && chown apache:webdev_warehouse /var/www/wsgi-scripts/warehouse/server/api/auth/secrets/saml-sp.key && chmod u-w /var/www/wsgi-scripts/warehouse/server/api/auth/secrets
      * cp -f /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/server/admin/etl/pentaho/kettle.properties_ConnectionDetails /var/www/wsgi-scripts/warehouse/server/admin/etl/pentaho/.

2. Configure Apache static content
   1. Specify currently installed version
      * See [Updating step 1.1 "Specify currently installed version"](#updating)
   2. Back up current content, for rollback

            mkdir -p /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/app-warehouse
            mv -f /var/www/html/app-warehouse/* /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/app-warehouse/.

   3. Deploy static content
      * see [Webapp deployment steps (Deployment step 3)](deployment.md#webapp)
   3. Restore web group ownership
      * chown -R :web_warehouse /var/www/html/app-warehouse/*
3. Configure Apache & reconfigure warehouse
   1. Specify currently installed version
      * See [Updating step 1.1 "Specify currently installed version"](#updating)
   2. Back up config, for rollback

            mkdir -p /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/etc/httpd/conf.d/
            mkdir -p /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/etc/security/limits.d/
            mv -f /etc/httpd/conf.d/wsgi.conf /etc/httpd/conf.d/wsgi-scripts.conf /etc/httpd/conf.d/wsgi-warehouse.conf /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/etc/httpd/conf.d/.
            mv -f /etc/security/limits.d/90-warehouse-nofile.conf /var/www/wsgi-scripts/warehouse/deploy_full_backup_${CURRENT_WH_VER}/etc/security/limits.d/.

   3. Deploy httpd config files
      - copy templates:

            sudo chown $USER /etc/security/limits.d
            cp /var/www/wsgi-scripts/warehouse/server/deploy/security/limits.d/* /etc/security/limits.d
            chmod o+r /etc/security/limits.d/*
            sudo chown -R root:root /etc/security/limits.d
            sudo chown $USER /etc/httpd/conf.d
            cp /var/www/wsgi-scripts/warehouse/server/deploy/httpd/conf.d/* /etc/httpd/conf.d/.
            sudo chown -R root:root /etc/httpd/conf.d
      - Update wsgi-warehouse.conf 'Listen' statement with Host IP & port virtualhost will run on
             - e.g.: Listen 10.0.80.120:80
      - Update wsgi-warehouse.conf VirtualHost directive with above IP+port
             - e.g.: `<VirtualHost 10.0.80.120:80>`
      - Update wsgi-warehouse.conf VirtualHost directive with ServerName
             - e.g.: ServerName warehouse.nwfsc.noaa.gov:80
      - Update logging path in wsgi-warehouse.conf VirtualHost directive
             - e.g.: ErrorLog logs/warehouse_error_log
             - e.g.: CustomLog logs/warehouse_access_log combined\

   4. Restart Apache server
      * sudo service httpd restart
   5. Test Warehouse web service operates
      * See: [Post Installation checklist](server/doc/Post_Install.md).
   6. Remove settings+full backups (Optional)
      1. Specify backup version to remove (e.g., for 'deploy_*_backup_1.1_2016-07-15T10:20-0700' enter '1.1')

                read -p "Enter backup IDs to remove: " WH_BACKUP_ID

      2. Delete
                rm -Rf /var/www/wsgi-scripts/warehouse/deploy_conf_backup_${WH_BACKUP_ID}*
                rm -Rf /var/www/wsgi-scripts/warehouse/deploy_full_backup_${WH_BACKUP_ID}*

### Rollback
1. Archive currently installed Warehouse content
   1. Enter a new archive ID

            read -p "Enter backup ID [e.g.: '1.1']: " WH_BACKUP_ID && ROLLBACK_WH_VER=${WH_BACKUP_ID}_$(date -I'minutes')

   2. Archive installed Warehouse

            mkdir -p /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}/app-warehouse
            mkdir -p /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}/etc/httpd/conf.d/
            mkdir -p /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}/etc/security/limits.d/
            mv -f /var/www/wsgi-scripts/warehouse/server /var/www/wsgi-scripts/warehouse/miniconda3 /var/www/wsgi-scripts/warehouse/Miniconda3-*-Linux-x86_64.sh /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}/.
            mv -f /var/www/html/app-warehouse/* /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}/app-warehouse/.
            mv -f /etc/httpd/conf.d/wsgi.conf /etc/httpd/conf.d/wsgi-scripts.conf /etc/httpd/conf.d/wsgi-warehouse.conf /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}/etc/httpd/conf.d/.
            mv -f /etc/security/limits.d/90-warehouse-nofile.conf /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}/etc/security/limits.d/.

2. Restore backup of previosu Warehouse content
   1. Enter ID of backup to restore

            read -p "Enter backup ID: " WH_RESTORE_ID

   2. Restore backup

            cp -Rf /var/www/wsgi-scripts/warehouse/deploy_full_backup_${WH_RESTORE_ID}*/server /var/www/wsgi-scripts/warehouse/deploy_full_backup_${WH_RESTORE_ID}*/miniconda3 /var/www/wsgi-scripts/warehouse/deploy_full_backup_${WH_RESTORE_ID}*/Miniconda3-*-Linux-x86_64.sh /var/www/wsgi-scripts/warehouse/.
            cp -Rf /var/www/wsgi-scripts/warehouse/deploy_full_backup_${WH_RESTORE_ID}*/app-warehouse/* /var/www/html/app-warehouse/.
            cp -f /var/www/wsgi-scripts/warehouse/deploy_full_backup_${WH_RESTORE_ID}*/etc/security/limits.d/90-warehouse-nofile.conf /etc/security/limits.d/.
            chmod o+r /etc/security/limits.d/*
            sudo chown -R root:root /etc/security/limits.d
            cp -f /var/www/wsgi-scripts/warehouse/deploy_full_backup_${WH_RESTORE_ID}*/etc/httpd/conf.d/* /etc/httpd/conf.d/.
            sudo chown -R root:root /etc/httpd/conf.d

3. Restart Apache server
      * sudo service httpd restart
4. Test rollback
   * See: [Post Installation checklist](server/doc/Post_Install.md).
5. (Optional) delete archive of the rolled-back Warehouse

        rm -Rf /var/www/wsgi-scripts/warehouse/rolled_back_full_${ROLLBACK_WH_VER}

### Uninstallation
To remove installed service:
```bash
#TBD
```

## Test
A Python _unittest_ functional test suite has been provided, to test a running instance of the FRAM Data Warehouse.

In the future this suite may be migrated to a set of Selenium WebClient scripts+hosted Selenium web testing environment, expanded to perform DB integration testing, etc.

### Test setup


Copyright (C) 2015-2019 ERT Inc.
