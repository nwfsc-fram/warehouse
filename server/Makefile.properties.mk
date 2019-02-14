# makefile defining workstation/developer-specific variables
#
# Copyright (C) 2015 ERT Inc.
#
# Instructions:
# Make your local changes to this file, then run:
#   git update-index --assume-unchanged Makefile.properties.mk
# (if you later want to modify the version controlled, base template you can
# revert, resume tracking, & make your edits to commit, via:
#   git checkout -- Makefile.properties.mk
#   git update-index --no-assume-unchanged Makefile.properties.mk
#   (edit the template file)
#   git commit Makefile.properties.mk
#   git update-index --assume-unchanged Makefile.properties.mk

# define credentials used to log into the Deploy destination
#  (deploy user is assumed to have sudo access to chown)
deploy_host = NwcDevFRAM.nwfsc.noaa.gov
deploy_user = bvanvaerenbergh
deploy_ssh_key = ~/.ssh/id_rsa
deploy_docker_port = 8081
deploy_docker_image = efhsite1

# define properties, used to install Warehouse server's CentOS 6 Apache content
deploy_install_dir_www_base = /var/www
deploy_install_dir_wgsi := ${deploy_install_dir_www_base}/wsgi-scripts/warehouse
deploy_install_dir_static := ${deploy_install_dir_www_base}/html/app-warehouse
deploy_install_dir_static_management := ${deploy_install_dir_www_base}/html/app-warehouse-management
deploy_install_user = root
deploy_install_dir_conf = /etc/httpd/conf.d

# define properties, used to configure Jenkins
jenkins_host = MyJenkinsHost.domain
jenkins_user = mylogin.tojenkinshost
jenkins_ssh_key = ${deploy_ssh_key}

# define properties, used to pretest current working copy
pretest_jenkins_job_param_name = pretest-data-warehouse.zip
pretest_jenkins_job_param_pull_conf = pull_config_db
pretest_jenkins_scheme = https
pretest_jenkins_host := ${jenkins_host}
pretest_jenkins_port = 8443
pretest_jenkins_job_token = ChangeMe!
