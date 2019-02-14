# -*- indent-tabs-mode:t; -*-
# Simple Makefile defining targets to build Anacondas virtualenv, run tests
#
# Copyright (C) 2015-2017 ERT Inc.
#

.PHONY: all build test

# Default target;
all:
	make build

all_build_dir = ../build
all_activate_virtualenv := source ${all_build_dir}/miniconda3/bin/activate test-env

all_conda_ver = 4.3.31
# target; construct Anacondas virtualenv
build:
	mkdir -p ${all_build_dir}/
	@echo 'Download Anaconda v3.18.9 micro installer & check package integrity'
	cd ${all_build_dir}/ && wget -c --ca-certificate=../test/repo_continuum_io.pem https://repo.continuum.io/miniconda/Miniconda3-${all_conda_ver}-Linux-x86_64.sh
	cd ${all_build_dir}/ && echo '7fe70b214bee1143e3e3f0467b71453c *Miniconda3-${all_conda_ver}-Linux-x86_64.sh' | md5sum -c -
	cd ${all_build_dir}/ && echo '5551f01f436b6409d467412c33e12ecc4f43b5e029290870f8fdeca403c274e6 *Miniconda3-${all_conda_ver}-Linux-x86_64.sh' | sha256sum -c -
	@echo 'Install Anaconda distribution'
	chmod +x ${all_build_dir}/Miniconda3-${all_conda_ver}-Linux-x86_64.sh
	- ${all_build_dir}/Miniconda3-${all_conda_ver}-Linux-x86_64.sh -b -p ${all_build_dir}/miniconda3
	- ${all_build_dir}/miniconda3/bin/conda env create --name test-env -f requirements-conda-env.yml
	@echo 'Install prequisite modules into virtualenv'
	bash -c '${all_activate_virtualenv} && pip install -r requirements.txt'

# target; run Python unittest cases from virtualenv
test:
	bash -c '${all_activate_virtualenv} && python3 -m unittest discover --failfast'

# target; clear build/temp files
clean:
	-rm -Rf ${all_build_dir}/
	-find . -name "*~" -delete
	-find . -name "*__pycache__" | xargs rm -rf
