# Makefile for ckanext-versions

PACKAGE_DIR := ckanext/external_storage
PACKAGE_NAME := ckanext.external_storage

SHELL := bash
PYTHON := python
PIP := pip
PIP_COMPILE := pip-compile
ISORT := isort
FLAKE8 := flake8
NOSETESTS := nosetests
PASTER := paster

# Find GNU sed in path (on OS X gsed should be preferred)
SED := $(shell which gsed sed | head -n1)

TEST_INI_PATH := ./test.ini
CKAN_PATH := ../ckan
SENTINELS := .make-status

PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print(sys.version_info[0])')


dev-requirements.%.txt: dev-requirements.in
	$(PIP_COMPILE) --no-index dev-requirements.in -o $@

requirements.%.txt: requirements.in
	$(PIP_COMPILE) --no-index requirements.in -o $@

$(SENTINELS):
	mkdir -p $@

$(SENTINELS)/test.ini: $(TEST_INI_PATH) $(CKAN_PATH)/test-core.ini | $(SENTINELS)
	$(SED) "s@use = config:.*@use = config:$(CKAN_PATH)/test-core.ini@" -i $(TEST_INI_PATH)
	@touch $@

$(SENTINELS)/requirements: requirements.py$(PYTHON_VERSION).txt dev-requirements.py$(PYTHON_VERSION).txt | $(SENTINELS)
	@touch $@

$(SENTINELS)/install: requirements.py$(PYTHON_VERSION).txt | $(SENTINELS)
	$(PIP) install -r requirements.py$(PYTHON_VERSION).txt
	@touch $@

$(SENTINELS)/develop: $(SENTINELS)/requirements $(SENTINELS)/install $(SENTINELS)/test.ini setup.py | $(SENTINELS)
	$(PIP) install -r dev-requirements.py$(PYTHON_VERSION).txt
	$(PIP) install -e .
	$(PASTER) --plugin=ckan db init -c $(TEST_INI_PATH)
	@touch $@

$(SENTINELS)/tests-passed: $(SENTINELS)/develop $(shell find $(PACKAGE_DIR) -type f) .flake8 .isort.cfg | $(SENTINELS)
	$(ISORT) -rc -df -c $(PACKAGE_DIR)
	$(FLAKE8) --statistics $(PACKAGE_DIR)
	$(NOSETESTS) --ckan \
	      --with-pylons=$(TEST_INI_PATH) \
          --nologcapture \
          --with-doctest
	@touch $@

.coverage: $(SENTINELS)/tests-passed $(shell find $(PACKAGE_DIR) -type f) .coveragerc
	$(NOSETESTS) --ckan \
	      --with-pylons=$(TEST_INI_PATH) \
          --nologcapture \
		  --with-coverage \
          --cover-package=$(PACKAGE_NAME) \
          --cover-inclusive \
          --cover-erase \
          --cover-tests

install: $(SENTINELS)/install
.PHONY: install

requirements: $(SENTINELS)/requirements
.PHONEY: requirements

develop: $(SENTINELS)/develop
.PHONEY: develop

test: $(SENTINELS)/tests-passed
.PHONY: test

coverage: .coverage
.PHONY: coverage
