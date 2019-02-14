# -*- indent-tabs-mode:t; -*-
# Simple Makefile for packaging & running FRAM Data Warehouse server
#
# Copyright (C) 2015-2017 ERT Inc.
# Authors: Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>

# for below targets, don't check any file modification times
.PHONY: build run test package pretest pull_config pull_config_db clean

# import workstation/developer specific settings
include Makefile.properties.mk

# default target; build application for local testing/evaluation
all:
	make build
all_build_dir = ../build
all_activate_virtualenv := source ${all_build_dir}/miniconda3/bin/activate warehouse-env

all_conda_ver = 4.3.31

build_data_integration_dir = admin/etl/pentaho/java
build_data_integraion_zipfile = pdi-ce-8.0.0.0-28.zip
# target; build FRAM Data Warehouse virtualenv
# skip requirements needed only for build testing:make build build_release=true
build:
	mkdir -p ${all_build_dir}/
	@echo 'Download Anaconda micro installer & check package integrity'
	# see conda changelog, for potential bug-fixes/new versions. https://github.com/conda/conda/blob/master/CHANGELOG.txt
	cd ${all_build_dir}/ && wget -c --ca-certificate=../server/repo_continuum_io.pem https://repo.continuum.io/miniconda/Miniconda3-${all_conda_ver}-Linux-x86_64.sh
	cd ${all_build_dir}/ && echo '7fe70b214bee1143e3e3f0467b71453c *Miniconda3-${all_conda_ver}-Linux-x86_64.sh' | md5sum -c -
	cd ${all_build_dir}/ && echo '5551f01f436b6409d467412c33e12ecc4f43b5e029290870f8fdeca403c274e6 *Miniconda3-${all_conda_ver}-Linux-x86_64.sh' | sha256sum -c -
	@echo 'Install Anaconda distribution'
	chmod +x ${all_build_dir}/Miniconda3-${all_conda_ver}-Linux-x86_64.sh
	- ${all_build_dir}/Miniconda3-${all_conda_ver}-Linux-x86_64.sh -b -p ${all_build_dir}/miniconda3
	- ${all_build_dir}/miniconda3/bin/conda env create --name warehouse-env -f requirements-conda-env.yml
	@echo "Remove previous assets from: 'build/server'" #no longer needed
	-rm -Rf ${all_build_dir}/server
	@echo 'Install prequisite modules into virtualenv'
ifndef build_release
	bash -c '${all_activate_virtualenv} && pip install --upgrade --no-binary lxml,xmlsec -r requirements-dev.txt'
else
	bash -c '${all_activate_virtualenv} && pip install --upgrade --no-binary lxml,xmlsec -r requirements.txt'
endif
	@echo 'Download Pentaho data-integration tools pack'
	mkdir -p ${build_data_integration_dir}
	if test -s ${build_data_integration_dir}/${build_data_integraion_zipfile}; then \
	  echo 'File already exists, skipping download.'; \
	else cd ${build_data_integration_dir} && wget --max-redirect=60 -c https://sourceforge.net/projects/pentaho/files/Pentaho%208.0/client-tools/${build_data_integraion_zipfile}/download -O ${build_data_integraion_zipfile} ; \
	fi
	cd ${build_data_integration_dir} && echo '0332aa527f69ebd3224ffea5bbb451f032b0fda6  ${build_data_integraion_zipfile}' | sha1sum -c -
	cd ${build_data_integration_dir} && echo '52333d725523c9f3cb86b66eee768872660462484feabc78e9d402a4506fb5a6  ${build_data_integraion_zipfile}' | sha256sum -c -

# target; run application locally, from virtualenv
run:
	bash -c '${all_activate_virtualenv} && python3 server.py'

# target; run Python unittest cases from virtualenv
test_module = "discover" #specify a module to test as: make test test_module=my/test.py
skip_lint = "false" #run Pylint by default
test:
	if [ "${skip_lint}" == "false" ]; then \
		echo 'Start static Python code analysis:'; \
		bash -c '${all_activate_virtualenv} && pylint -j 2 mod_wsgi_application.py wsgiApps.py server.py api admin'; \
	else \
		echo '(!Skipping static Python code analysis)'; \
	fi
	- mkdir -p work/ #back up the developers db config settings
	- [ ! -e work/db_config.ini ] && mv -f db_config.ini work/. #if they're not already backed up
	- [ ! -e work/db_dwsupport.ini ] && mv -f db_dwsupport.ini work/.
	git checkout db_config.ini db_dwsupport.ini #restore Empty db settings from Git
	@echo '${test_module}'
	bash -c '${all_activate_virtualenv} && python3 -m unittest ${test_module}'; \
		status=$$?; \
		mv -f work/db_config.ini work/db_dwsupport.ini work/db_dwsensitive.ini . ; \
		exit $$status #restore the original developer configs, even if test failed

package_tarball_name = warehouse-server.tgz

# target; package build for deploy
package:
	make build build_release=yes
	cd ${all_build_dir}/ && tar czf ${package_tarball_name} miniconda3 ../server Miniconda3-${all_conda_ver}-Linux-x86_64.sh
	sha256sum ${all_build_dir}/${package_tarball_name}

# obtain security HTTP header from Jenkins
pretest_csrf_header := $(shell wget -q --no-check-certificate --output-document - '${pretest_jenkins_scheme}://${pretest_jenkins_host}:${pretest_jenkins_port}/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)' )
# set a pretest comment
pretest_build_comment := $(shell echo 'Developer+Build:+started+%5B'$$(date +%D-%T+%Z)'%5D+for+'$$(git config user.name)'+%3C'$$(git config user.email)'%3E')
pull_config_db = true

# target; pretests the current working copy via a remote Jenkins CI server
pretest:
	## pack working copy into a ZIP (must pack up one level, jenkins checks out project root)
	-rm -Rf work/
	-mkdir -p work
	cd .. && zip -r --exclude='build/*' --exclude=server/work/${pretest_jenkins_job_param_name} server/work/${pretest_jenkins_job_param_name} server/. test/. .git/.
	## trigger build via job Token and CSRF crumb
	## per: https://wiki.jenkins-ci.org/display/JENKINS/Remote+access+API#RemoteaccessAPI-Submittingjobs
	curl -X POST --insecure -sSL --header ${pretest_csrf_header} \
	--form json='{"parameter": [{"name":"${pretest_jenkins_job_param_name}", "file":"file0"}'\
',{"name":"${pretest_jenkins_job_param_pull_conf}", "value":"${pull_config_db}"}]}' \
	--form file0=@work/${pretest_jenkins_job_param_name} \
	'${pretest_jenkins_scheme}://${pretest_jenkins_host}:${pretest_jenkins_port}/job/warehouse-server/build?token=${pretest_jenkins_job_token}&cause=${pretest_build_comment}&delay=0sec'

# create Apache WSGI content dir
deploy_install_cmd_1 := sudo chown -R ${deploy_user} ${deploy_install_dir_www_base} && mkdir -p ${deploy_install_dir_wgsi} #TODO: check/attempt install of apache+python36-mod_wsgi
# extract the deploy package, streamed to destination over SSH
# (Anacondas environments are not portable; reinstall.)
deploy_install_anacondas_workaround_1 = rm -Rf ${deploy_install_dir_wgsi}/envs || true && mv ${deploy_install_dir_wgsi}/miniconda3/envs ${deploy_install_dir_wgsi}/. && rm -Rf ${deploy_install_dir_wgsi}/miniconda3 && ${deploy_install_dir_wgsi}/Miniconda3-${all_conda_ver}-Linux-x86_64.sh -b -p ${deploy_install_dir_wgsi}/miniconda3 && mv ${deploy_install_dir_wgsi}/envs ${deploy_install_dir_wgsi}/miniconda3/.
deploy_install_cmd_2 := tar xzf - --directory=${deploy_install_dir_wgsi} && ${deploy_install_anacondas_workaround_1}
# Install Apache static content, & set ownership
deploy_install_cmd_3 := rm -Rf ${deploy_install_dir_static} || true && \
                        mv -f ${deploy_install_dir_wgsi}/server/app \
                              ${deploy_install_dir_static} && \
                        rm -Rf ${deploy_install_dir_static_management} || true && \
                        mv -f ${deploy_install_dir_wgsi}/server/management_app \
                              ${deploy_install_dir_static_management} && \
                        sudo chown -R ${deploy_install_user}:${deploy_install_user} \
                              ${deploy_install_dir_wgsi} && \
                        sudo chmod -R o+rx ${deploy_install_dir_wgsi} \
                                           ${deploy_install_dir_static} \
                                           ${deploy_install_dir_static_management}
# install Apache configuration, & set ownership
deploy_install_cmd_4 := sudo chown -R ${deploy_user} ${deploy_install_dir_conf} && cp -f ${deploy_install_dir_wgsi}/server/deploy/httpd/conf.d/* ${deploy_install_dir_conf}/. && sudo chown -R ${deploy_install_user}:${deploy_install_user} ${deploy_install_dir_conf}

# target; install service to a destination CentOS 6 system, specified in Makefile.properties.mk
deploy_install: Makefile.properties.mk ${all_build_dir}/${package_tarball_name}
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "${deploy_install_cmd_1}"
	@echo transmitting Warehouse package:
	sha256sum ${all_build_dir}/${package_tarball_name}
	cat ${all_build_dir}/${package_tarball_name} | ssh -i ${deploy_ssh_key} -o Compression=no ${deploy_user}@${deploy_host} "${deploy_install_cmd_2}"
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "${deploy_install_cmd_3}"
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "${deploy_install_cmd_4}"
	make deploy_config

# back up existing config files & prep tmp dir
deploy_cmd_1 := sudo chown -R ${deploy_user} \
                       ${deploy_install_dir_wgsi} \
                       ${deploy_install_dir_static} \
                       ${deploy_install_dir_static_management} && \
                if test -e ${deploy_install_dir_wgsi}/deploy_conf_backup/ ; then \
                  echo 'Using existing conf backup (aborted deploy?): ${deploy_install_dir_wgsi}/deploy_conf_backup'; \
                  else mkdir ${deploy_install_dir_wgsi}/deploy_conf_backup/ && \
                    cp -f ${deploy_install_dir_wgsi}/server/server.ini \
                          ${deploy_install_dir_wgsi}/server/db_config.ini \
                          ${deploy_install_dir_wgsi}/server/db_dwsensitive.ini \
                          ${deploy_install_dir_wgsi}/server/db_dwsupport.ini \
                          ${deploy_install_dir_wgsi}/deploy_conf_backup/. && \
                    cp -f ${deploy_install_dir_wgsi}/server/api/auth/saml-sp.crt \
                          ${deploy_install_dir_wgsi}/server/api/auth/secrets/saml-sp.key \
                          ${deploy_install_dir_wgsi}/server/openssl-keystore.jks \
                          ${deploy_install_dir_wgsi}/deploy_conf_backup/. || true; \
                fi && \
                rm -Rf ${deploy_install_dir_wgsi}/server \
                       ${deploy_install_dir_wgsi}/miniconda3 \
                       ${deploy_install_dir_wgsi}/Miniconda3-${all_conda_ver}-Linux-x86_64.sh
# restore config file backup
deploy_cmd_2 := sudo chown -R ${deploy_user} \
                       ${deploy_install_dir_wgsi}/server && \
                cp -f ${deploy_install_dir_wgsi}/deploy_conf_backup/*.ini \
                      ${deploy_install_dir_wgsi}/deploy_conf_backup/*.jks \
                      ${deploy_install_dir_wgsi}/server/. && \
                cp -f ${deploy_install_dir_wgsi}/deploy_conf_backup/saml-sp.crt \
                      ${deploy_install_dir_wgsi}/server/api/auth/. && \
                UMASK_PREV=$$(umask) && umask 077 && \
                mkdir -p /var/www/wsgi-scripts/warehouse/server/api/auth/secrets || true && \
                umask 277 && \
                cp -f ${deploy_install_dir_wgsi}/deploy_conf_backup/saml-sp.key \
                      ${deploy_install_dir_wgsi}/server/api/auth/secrets/. && \
                umask $$UMASK_PREV && \
                sudo chmod o+rx ${deploy_install_dir_wgsi}/server/api/auth/* && \
                sudo chown -R ${deploy_install_user}:${deploy_install_user} \
                       ${deploy_install_dir_wgsi} \
                       ${deploy_install_dir_static} \
                       ${deploy_install_dir_static_management} && \
               sudo chown apache \
                       ${deploy_install_dir_wgsi}/server/api/auth/secrets/saml-sp.key \
                       ${deploy_install_dir_wgsi}/server/openssl-keystore.jks && \
               sudo service httpd restart && \
               curl --insecure https://${deploy_host}/api/v1/source && \
               sleep 3m && \
               sudo chown -R ${deploy_user} \
                      ${deploy_install_dir_wgsi}/deploy_conf_backup && \
               sudo chown ${deploy_user} ${deploy_install_dir_wgsi} && \
               rm -Rf ${deploy_install_dir_wgsi}/deploy_conf_backup && \
               sudo chown ${deploy_install_user} ${deploy_install_dir_wgsi}

# target; deploy current package to a remote service install, specified in Makefile.properties.mk
deploy: Makefile.properties.mk ${all_build_dir}/${package_tarball_name}
	# back up remote WSGI app config, & prep for package rollout
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "${deploy_cmd_1}"
	# deploy package, as per target: deploy_install
	@echo transmitting Warehouse package:
	sha256sum ${all_build_dir}/${package_tarball_name}
	cat ${all_build_dir}/${package_tarball_name} | ssh -i ${deploy_ssh_key} -o Compression=no ${deploy_user}@${deploy_host} "${deploy_install_cmd_2}"
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "${deploy_install_cmd_3}"
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "${deploy_install_cmd_4}"
	# restore original WSGI app config
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "${deploy_cmd_2}"

# target; deploy current package to a local Docker container
deploy_docker: Makefile.properties.mk Dockerfile ${all_build_dir}/${package_tarball_name}
	# build container
	docker build -t centos6-httpd-warehouse-${deploy_docker_image} .
	# TODO: deploy package, as per target: deploy_install
	# run the container
	-docker rm -f warehouse-server-${deploy_docker_image}
	docker run -d -p ${deploy_docker_port}:80 --restart=always --name warehouse-server-${deploy_docker_image} centos6-httpd-warehouse-${deploy_docker_image} /run-httpd.sh

# target; push local configuration, to remote install specified in Makefile.properties.mk
deploy_config: Makefile.properties.mk server.ini db_config.ini db_dwsensitive.ini db_dwsupport.ini openssl-keystore.jks
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "sudo chown -R ${deploy_user} ${deploy_install_dir_wgsi}"
	scp -i ${deploy_ssh_key} server.ini db_config.ini db_dwsensitive.ini db_dwsupport.ini openssl-keystore.jks ${deploy_user}@${deploy_host}:${deploy_install_dir_wgsi}/server/.
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "sudo chown -R ${deploy_install_user} ${deploy_install_dir_wgsi}"

# target; pull down configuration from remote install, specified in Makefile.properties.mk
pull_config:
	@echo assume ownership of Java keystore
	ssh -i ${deploy_ssh_key} -t -t ${deploy_user}@${deploy_host} "sudo chown ${deploy_user} ${deploy_install_dir_wgsi}/server/openssl-keystore.jks"
	@echo retrive config files
	scp -i ${deploy_ssh_key} '${deploy_user}@${deploy_host}:${deploy_install_dir_wgsi}/server/*.ini' \
    	'${deploy_user}@${deploy_host}:${deploy_install_dir_wgsi}/server/openssl-keystore.jks' .
	@echo restore Java keystore ownership
	ssh -i ${jenkins_ssh_key} -t -t ${deploy_user}@${deploy_host} "sudo chown apache ${deploy_install_dir_wgsi}/server/openssl-keystore.jks"

# target; pull down the DB configuration from remote install, specified in Makefile.properties.mk
pull_config_db:
	scp -i ${deploy_ssh_key} '${deploy_user}@${deploy_host}:${deploy_install_dir_wgsi}/server/db_*.ini' .

pull_cmd_1 := sudo chown -R ${jenkins_user} ~jenkins/jobs
pull_cmd_2 := sudo chown -R jenkins ~jenkins/jobs

# target; pull Jenkins job configuration down from CI server
pull_jenkins:
	@echo authenticate via SSH to retrieve a copy of current Jenkins config
	ssh -i ${jenkins_ssh_key} -t -t ${jenkins_user}@${jenkins_host} "${pull_cmd_1}"
	scp -i ${jenkins_ssh_key} ${jenkins_user}@${jenkins_host}:/var/lib/jenkins/jobs/warehouse-server/config.xml jenkins/warehouse-server/.
	ssh -i ${jenkins_ssh_key} -t -t ${jenkins_user}@${jenkins_host} "${pull_cmd_2}"

# target; clean up text-editor temporary files, build, & compiled bytecode
clean:
	-find . -name "*~" -delete
	-rm -Rf ${all_build_dir}/
	-rm -Rf work/
	-find . -name "*__pycache__" | xargs rm -rf
