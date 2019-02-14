# Production Deployment

## Component Overview
- [Webserver](#webserver) - general Apache setup
    - [API](#api) - Python webservice layer
    - [Webapp](#webapp) - rich mapping tool & EFH-Catalog pages
- [Post-install](#post-install) - post deployment checklists

## Webserver
The process for installing the Warehouse service release package on a CentOS 6 host is documented below.

:exclamation: *NOTE: before proceeding with installation of new API or Webapp, first ensure the new components are compatible with the installed DW database version \[see Section: [Database](#database)\]* :exclamation:

#### Installation Prerequisites
Environment must be prepared with the following files & software (including CentOS 6 OS) before continuing.

|Required software:|
-------
|CentOS 6.6+|
|Apache2|
|postgresql-devel package|
|libxml2-devel package|
|libxslt-devel package|
|xmlsec1-devel package|
|xmlsec1-openssl-devel package|
|libtool-ltdl-devel packages package|
|mod_wsgi v4.5.24+ running Anaconda Python 3.6.4 (see: [FRAM mod_wsgi setup directions](https://nwcgit.nwfsc.noaa.gov/fram-data/mod_wsgi/blob/master/README.md))|
|openjdk-8-jre package|

Required files:
  1. obtain _warehouse-server.tgz_ installation package
     * see [latest build download](https://nwcdevfram.nwfsc.noaa.gov:8443/job/warehouse-server/lastSuccessfulBuild/artifact/warehouse/server/build/warehouse-server.tgz)
     * see [build checksum + latest build release date](https://nwcdevfram.nwfsc.noaa.gov:8443/job/warehouse-server/lastSuccessfulBuild/artifact/warehouse/server/build/warehouse-server.tgz/*fingerprint*/)
Optional files:
  1. obtain _warehouse-sensitive.tgz_ installation package.
  2. obtain _efh-catalog-static-*.zip_ Essential Fish Habitat web content package
     * -see [NwcGit download](https://nwcgit.nwfsc.noaa.gov/fram-data/efh-catalog-static/repository/archive.zip)- GitLab download does not seem to be working
     * run: git archive --remote git@nwcgit.nwfsc.noaa.gov:fram-data/efh-catalog-static.git --format tar HEAD -o efh-catalog-static.tar
  3. Private key & signed certificate files, for SAML "Service Provider"

#### Configure Reverse Proxy
1. Configure public-facing Reverse Proxy server
    1. Configure Warehouse service server host in: _/etc/hosts_
    2. Ensure apache mod_rewrite is loaded into the Reverse Proxy server and RewriteEngine is turned on.
    3. Add to reverse-proxy httpd config:

            RewriteRule ^/data$ /data/ [R]
            ProxyPass /data/ http://warehouse-host-name.nwfsc.noaa.gov/
            ProxyPassReverse /data/ http://warehouse-host-name.nwfsc.noaa.gov/

    ### API
2. Deploy Warehouse release package
   1. Create Apache web content dir

            sudo service stop apache
            chown -R $USER /var/www #temporarily assume ownership
            mkdir -p /var/www/wsgi-scripts/warehouse

   2. Untar install package

            tar xzf /path/to/warehouse-server.tgz --directory=/var/www/wsgi-scripts/warehouse

   3. Reinstall Continuum Analytics Anaconda
      1. back up package environment and clear Anaconda dir

            mv /var/www/wsgi-scripts/warehouse/miniconda3/envs /var/www/wsgi-scripts/warehouse/.
            rm -Rf /var/www/wsgi-scripts/warehouse/miniconda3

      2. run installer

            /var/www/wsgi-scripts/warehouse/Miniconda3-*-Linux-x86_64.sh -b -p /var/www/wsgi-scripts/warehouse/miniconda3

      3. replace package environment

            mv -f /var/www/wsgi-scripts/warehouse/envs /var/www/wsgi-scripts/warehouse/miniconda3/.

   4. Install Apache configuration

            sudo chown $USER /etc/httpd/conf.d
            cp /var/www/wsgi-scripts/warehouse/server/deploy/httpd/conf.d/* /etc/httpd/conf.d/.
            sudo chown -R root:root /etc/httpd/conf.d
      * Update wsgi-warehouse.conf 'Listen' statement with Host IP & port virtualhost will run on
            - e.g.: Listen 10.0.80.120:80
      * Update wsgi-warehouse.conf VirtualHost directive with above IP+port
            - e.g.: `<VirtualHost 10.0.80.120:80>`
      * Update wsgi-warehouse.conf VirtualHost directive with ServerName
            - e.g.: ServerName warehouse.nwfsc.noaa.gov:80
      * Update logging path in wsgi-warehouse.conf VirtualHost directive
            - e.g.: ErrorLog logs/warehouse_error_log
            - e.g.: CustomLog logs/warehouse_access_log combined
      * Delete wsgi-warehouse.conf Dev-environment HTTPS directives (1 of 2)
            - starting with: `## START: DEV-ENVIRONMENT APACHE HTTPS DIRECTIVES 1of2 #`
            - through: `## END: DEV-ENVIRONMENT APACHE HTTPS DIRECTIVES 1of2 #`
      * Delete wsgi-warehouse.conf Dev-environment HTTPS directives (2 of 2)
            - starting with: `## START: DEV-ENVIRONMENT APACHE HTTPS DIRECTIVES 2of2 #`
            - through: `## END: DEV-ENVIRONMENT APACHE HTTPS DIRECTIVES 2of2 #`

   5. Configure Apache file limits

            sudo chown $USER /etc/security/limits.d
            cp /var/www/wsgi-scripts/warehouse/server/deploy/security/limits.d/* /etc/security/limits.d
            chmod o+r /etc/security/limits.d/*
            sudo chown -R root:root /etc/security/limits.d

   5. Configure libxml2 shared library

            sudo chown $USER /etc/ld.so.conf.d
            cp /var/www/wsgi-scripts/warehouse/server/deploy/ld.so.conf.d/*  /etc/ld.so.conf.d
            sudo chmod o+r /etc/ld.so.conf.d/warehouse-x86_64.conf
            sudo chown -R root:root /etc/ld.so.conf.d
            sudo ldconfig

   6. Configure API service
     1. Configure 'proxy_url_base' with the (Apache) base URL the service has been installed as.
       * /var/www/wsgi-scripts/warehouse/server/server.ini

   7. Configure databases (Network routes must be open/firewalls configured to permit connection).
      1. Configure Warehouse db connection:
         * /var/www/wsgi-scripts/warehouse/server/db_config.ini
         * encode db_config.ini password via properties: 'ciphertext_key' & 'ciphertext' using provided tool:

                   cd /var/www/wsgi-scripts/warehouse/server/api
                   PYTHONPATH=/var/www/wsgi-scripts/warehouse/server:/var/www/wsgi-scripts/warehouse/miniconda3/envs/warehouse-env/lib/python3.6/site-packages /var/www/wsgi-scripts/modwsgi_python/miniconda3/bin/python aes.py
                   #Enter db connection password:
                   #Re-enter password, to confirm:
                   #Warehouse API .ini password parameters (paste both into .ini file):
                   #ciphertext_key = b'\x00\x00 ... \x00'
                   #ciphertext = b'\x00\x00 ... \x00'
                   source deactivate

      2. Configure Warehouse db managment connection
         * /var/www/wsgi-scripts/warehouse/server/db_dwsupport.ini
         * encode db_dwsupport.ini password via properties: 'ciphertext_key' & 'ciphertext' using provided tool:

                   cd /var/www/wsgi-scripts/warehouse/server/api
                   PYTHONPATH=/var/www/wsgi-scripts/warehouse/server:/var/www/wsgi-scripts/warehouse/miniconda3/envs/warehouse-env/lib/python3.6/site-packages /var/www/wsgi-scripts/modwsgi_python/miniconda3/bin/python aes.py
                   #Enter db connection password:
                   #Re-enter password, to confirm:
                   #Warehouse API .ini password parameters (paste both into .ini file):
                   #ciphertext_key = b'\x00\x00 ... \x00'
                   #ciphertext = b'\x00\x00 ... \x00'
                   source deactivate

   7. Configure SAML "Service Provider" signed certificate

            cp /my/certfile/path/saml-sp.crt /var/www/wsgi-scripts/warehouse/server/api/auth/saml-sp.crt
            # deploy secret key file
            UMASK_PREV=$(umask)
            umask 0277
            mkdir -p /var/www/wsgi-scripts/warehouse/server/api/auth/secrets
            cp /my/certfile/path/saml-sp.key /var/www/wsgi-scripts/warehouse/server/api/auth/secrets/saml-sp.key
            umask $UMASK_PREV

   8. Configure Pentaho scheduled jobs
      1. Prepare two Pentaho java key management passwords, and document in a secure location:
         * OpenSSL key access password: ______________________
         * keytool password, for keystore contents validation: __________________
      2. Import webserver public certificate & HTTPS secret key:
         * Prepare a temporary pkcs12 encoded file, with below command. Provide the OpenSSL key access password (from step1) when prompted.

                   openssl pkcs12 -inkey location/to/https/secrets/server.key -in location/to/https/server.crt -export -out temp-jetty.pkcs12

         * Build java keystore, via the following commands. When prompted, provide the keytool password (from step1) twice, then provide the OpenSSL key access password.

                   keytool -importkeystore -srckeystore temp-jetty.pkcs12 -srcstoretype PKCS12 -destkeystore /var/www/wsgi-scripts/warehouse/server/openssl-keystore.jks
                   #Enter destination keystore password:  
                   #Re-enter new password:
                   #Enter source keystore password:
                   #Entry for alias 1 successfully imported.
                   #Import command completed:  1 entries successfully imported, 0 entries failed or cancelled
                   rm -f temp-jetty.pkcs12 #(clean up temp file)

      3. Configure keytool & OpenSSL key passwords
         * Encode keytool verification password:

                   java -cp /tmp/warehouse-carte-9443/data-integration/lib/jetty-util-8.1.15.v20140411.jar org.eclipse.jetty.util.security.Password MySecureKeystorePw1
                   #MySecureKeystorePw1
                   #OBF:1e3f20ld1ldu1t331v8w1y851ym51vu91rv51t331rxp1vv11ym91y7t1v9q1t331ldo20l91e1v
                   #MD5:01e82cd698cefd5abff8705f2da8a2c5

         * Enter the 2nd line of java output as the `etl.pentaho.https.jks_pw` value in: /var/www/wsgi-scripts/warehouse/server/server.ini
         * Encode OpenSSL key access password

                   java -cp /tmp/warehouse-carte-9443/data-integration/lib/jetty-util-8.1.15.v20140411.jar org.eclipse.jetty.util.security.Password MyAmazingOpensslPw1
                   #MyAmazingOpensslPw1
                   #OBF:1e3f20ld1htc1w1s1v1p20061vne1uvc1vna1ke71vns1uuu1vno1zzs1v2p1w1q1hu620l91e1v
                   #MD5:9f3d7c68abd8d500de5c4ab3dbe6488c

         * Enter the 2nd line of java output as the `etl.pentaho.https.openssl_pw` value in: /var/www/wsgi-scripts/warehouse/server/server.ini
         * Enter the full keystore file path (`/var/www/wsgi-scripts/warehouse/server/openssl-keystore.jks`) as the `etl.pentaho.https.keystore` value in: `/var/www/wsgi-scripts/warehouse/server/server.ini`

    ### Webapp
3. Configure Apache static content

            Static content        |location                           |instructions
            ----------------------|-----------------------------------|----
            Webapp resources      | `/var/www/html/app-warehouse`     | (link): [Deploy webapp files](#webapp)
            Essential Fish Habitat| `/var/www/html/efh-catalog-static`| (link): [Deploy Essential Fish Habitat](#essential-fish-habitat)
            Management Webapp resources| `/var/www/html/app-warehouse-management`| (link): [Deploy Management webapp files](#management-webapp)

   1. Deploy webapp files to: `/var/www/html/app-warehouse/`
      * mv /var/www/wsgi-scripts/warehouse/server/app/* /var/www/html/app-warehouse/.
   2. Edit files:
     1. Enable Production analytics in /var/www/html/app-warehouse/index.html
         * Delete line: "<!-- Google Analytics for production. Uncomment for production."
         * leave the next line. (This is the Production analytics script)
         * Delete the following line: "-->"
     2. Remove Development analytics code block from /var/www/html/app-warehouse/index.html
         * Delete 13 lines, starting with: "<!--Analytics for DEV/TEST environment. Remove before moving to PROD -->"
         * including the final Dev analytics code block line: "<!-- END DEV/TEST analytics script  -->"
     3. Configure the base production URL path in /var/www/html/app-warehouse/index.html
         * replace index.html element: \<base href="/"\> URL with the path from production URL
         - e.g.: set to \<base href="/data/">, when installed at https://www.nwfsc.noaa.gov/data/
     4. Configure the base production full URL in /var/www/html/app-warehouse/view1/view1.js
         * replace 'devwww11' URL with production URL
     5. Configure the full production base URL in /var/www/html/app-warehouse/efh-catalog/angular/controller_metadata.js
         * replace 'http://NwcDevFRAM.nwfsc.noaa.gov' with the base production URL
         - e.g.: https://www.nwfsc.noaa.gov/data [No trailing slash]
     6. Configure the full production base URL in /var/www/html/app-warehouse/efh-catalog/script/efh_catalog_page.js
         * replace 'http://NwcDevFRAM.nwfsc.noaa.gov' with the base production URL
   3. Set web content ownership + permissions:

            chown -R :webdev_warehouse /var/www/html/app-warehouse/* #restore Group write-access for Dev team (1of2)
            chmod -R g+rwx /var/www/html/app-warehouse/*             #restore Group write-access for Dev team (2of2)
            chmod -R o+rx /var/www/html/app-warehouse/*         #grant read-access to Apache web server
     _(If skipping Management Webapp files, continue on to step: [Essential Fish Habitat](#essential-fish-habitat))_
    #### Management Webapp
   4. Deploy management files to: `/var/www/html/app-warehouse-management/`
      * mv /var/www/wsgi-scripts/warehouse/server/management_app/* /var/www/html/app-warehouse-management/.
   2. Edit files:
     1. Configure the base production URL path in /var/www/html/app-warehouse-management/index.html
         * replace index.html element: \<base href="/management/"\> URL with the path from production URL
         - e.g.: set to \<base href="/data/management/">, when installed at https://www.nwfsc.noaa.gov/data/
     1. Configure the base production URL path in /var/www/html/app-warehouse-management/table.html
         * replace table.html element: \<base href="/management/"\> URL with the path from production URL
         - e.g.: set to \<base href="/data/management/">, when installed at https://www.nwfsc.noaa.gov/data/
   3. Set web content ownership + permissions:

            chown -R :webdev_warehouse /var/www/html/app-warehouse-management/* #restore Group write-access for Dev team (1of2)
            chmod -R g+rwx /var/www/html/app-warehouse-management/*             #restore Group write-access for Dev team (2of2)
            chmod -R o+rx /var/www/html/app-warehouse-management/*         #grant read-access to Apache web server
     _(If skipping Essential Fish Habitat files, continue on to final step: [Clean up](#clean-up))_
    #### Essential Fish Habitat
   4. Deploy Essential Fish Habitat static web content *(Note: EFH web content was also deployed in step 3.1; via subfolder app-warehouse/efh-catalog/)*
      * unzip efh-catalog-static-*.zip /var/www/html/
   5. Set EFH content ownership + permissions:

            chown -R :webdev_warehouse /var/www/html/efh-catalog-static/* #restore Group write-access for Dev team (1of2)
            chmod -R g+rwx /var/www/html/efh-catalog-static/*             #restore Group write-access for Dev team (2of2)
            chmod -R o+rx /var/www/html/efh-catalog-static/*         #grant read-access to Apache web server
    #### Clean up
   6. (Optional) Request Sysadmin's assistance, to normalize the file ownership for static web content:

            sudo chown -R root: /var/www/html/app-warehouse/* /var/www/html/app-warehouse-management/* /var/www/html/efh-catalog-static/* #restore uniform file ownership

    ### Post Install
4. See [README.md](README.md#production-installation) for instructions on starting, stopping & operating the service.

5. Complete [post-install checklist](server/doc/Post_Install.md).

#### Copyright (C) 2016-2019 ERT Inc.
