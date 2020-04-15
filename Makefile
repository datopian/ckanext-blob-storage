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
DOCKER_COMPOSE := docker-compose
GIT := git

# Find GNU sed in path (on OS X gsed should be preferred)
SED := $(shell which gsed sed | head -n1)

TEST_INI_PATH := ./test.ini
SENTINELS := .make-status

PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print(sys.version_info[0])')

# CKAN environment variables
CKAN_PATH := ckan
CKAN_REPO_URL := https://github.com/ckan/ckan.git
CKAN_VERSION := ckan-2.8.3
CKAN_CONFIG_FILE := $(CKAN_PATH)/development.ini
CKAN_SITE_URL := http://localhost:5000
POSTGRES_USER := ckan
POSTGRES_PASSWORD := ckan
POSTGRES_DB := ckan
CKAN_SOLR_PASSWORD := ckan
DATASTORE_DB_NAME := datastore
DATASTORE_DB_RO_USER := datastore_ro
DATASTORE_DB_RO_PASSWORD := datastore_ro
CKAN_LOAD_PLUGINS := external_storage authz_service stats text_view image_view recline_view datastore


dev-requirements.%.txt: dev-requirements.in
	$(PIP_COMPILE) --no-index dev-requirements.in -o $@

requirements.%.txt: requirements.in
	$(PIP_COMPILE) --no-index requirements.in -o $@

.coverage: $(SENTINELS)/tests-passed $(shell find $(PACKAGE_DIR) -type f) .coveragerc
	$(NOSETESTS) --ckan \
	      --with-pylons=$(TEST_INI_PATH) \
          --nologcapture \
		  --with-coverage \
          --cover-package=$(PACKAGE_NAME) \
          --cover-inclusive \
          --cover-erase \
          --cover-tests

## Update requirements files for the current Python version
requirements: $(SENTINELS)/requirements
.PHONEY: requirements

## Install this extension to the current Python environment
install: $(SENTINELS)/install
.PHONY: install

## Set up the extension for development in the current Python environment
develop: $(SENTINELS)/develop
.PHONEY: develop

## Run all tests
test: $(SENTINELS)/tests-passed
.PHONY: test

## Run test coverage report
coverage: .coverage
.PHONY: coverage

$(CKAN_PATH):
	$(GIT) clone $(CKAN_REPO_URL) $@

$(CKAN_CONFIG_FILE): $(SENTINELS)/ckan-installed $(SENTINELS)/develop | _check_virtualenv
	$(PASTER) make-config --no-interactive ckan $(CKAN_CONFIG_FILE)
	$(PASTER) --plugin=ckan config-tool $(CKAN_CONFIG_FILE) \
		debug=true \
		ckan.site_url=$(CKAN_SITE_URL) \
		sqlalchemy.url=postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost/$(POSTGRES_DB) \
		ckan.datastore.write_url=postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost/$(DATASTORE_DB_NAME) \
		ckan.datastore.read_url=postgresql://$(DATASTORE_DB_RO_USER):$(DATASTORE_DB_RO_PASSWORD)@localhost/$(DATASTORE_DB_NAME) \
		ckan.plugins='$(CKAN_LOAD_PLUGINS)' \
		ckan.storage_path='%(here)s/storage' \
		solr_url=http://127.0.0.1:8983/solr/ckan \
		ckanext.external_storage.storage_service_url=http://localhost:9419

## Install the right version of CKAN into the virtual environment
ckan-install: $(SENTINELS)/ckan-installed
	@echo "Current CKAN version: $(shell cat $(SENTINELS)/ckan-version)"
.PHONY: ckan-install

## Run CKAN in the local virtual environment
ckan-start: $(SENTINELS)/ckan-installed $(SENTINELS)/install-dev $(CKAN_CONFIG_FILE) | _check_virtualenv
	$(PASTER) --plugin=ckan db init -c $(CKAN_CONFIG_FILE)
	$(PASTER) --plugin=ckan serve --reload $(CKAN_CONFIG_FILE)
.PHONY: ckan-start

.env:
	@___POSTGRES_USER=$(POSTGRES_USER) \
	___POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
	___POSTGRES_DB=$(POSTGRES_DB) \
	___CKAN_SOLR_PASSWORD=$(CKAN_SOLR_PASSWORD) \
	___DATASTORE_DB_NAME=$(DATASTORE_DB_NAME) \
	___DATASTORE_DB_USER=$(POSTGRES_USER) \
	___DATASTORE_DB_RO_USER=$(DATASTORE_DB_RO_USER) \
	___DATASTORE_DB_RO_PASSWORD=$(DATASTORE_DB_RO_PASSWORD) \
	env | grep ^___ | $(SED) 's/^___//' > .env
	@cat .env

## Start all Docker services
docker-up: .env
	$(DOCKER_COMPOSE) up -d
	@until $(DOCKER_COMPOSE) exec db pg_isready -U $(POSTGRES_USER); do sleep 1; done
	@sleep 2
	@echo " \
    	CREATE ROLE $(DATASTORE_DB_RO_USER) NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN PASSWORD '$(DATASTORE_DB_RO_PASSWORD)'; \
    	CREATE DATABASE $(DATASTORE_DB_NAME) OWNER $(POSTGRES_USER) ENCODING 'utf-8'; \
    	GRANT ALL PRIVILEGES ON DATABASE $(DATASTORE_DB_NAME) TO $(POSTGRES_USER);  \
    " | $(DOCKER_COMPOSE) exec -T db psql --username "$(POSTGRES_USER)"
.PHONY: docker-up

## Stop all Docker services
docker-down: .env
	$(DOCKER_COMPOSE) down
.PHONY: docker-down

## Initialize the development environment
dev-setup: _check_virtualenv $(SENTINELS)/ckan-installed $(CKAN_PATH)/who.ini $(CKAN_CONFIG_FILE) $(SENTINELS)/develop
.PHONY: setup

## Start a full development environment
dev-start: dev-setup docker-up ckan-start
.PHONY: start-dev

# Private targets

_check_virtualenv:
	@if [ -z "$(VIRTUAL_ENV)" ]; then \
	  echo "You are not in a virtual environment - activate your virtual environment first"; \
	  exit 1; \
	fi
.PHONY: _check_virtualenv

$(SENTINELS):
	mkdir -p $@

$(SENTINELS)/ckan-version: $(CKAN_PATH) | _check_virtualenv $(SENTINELS)
	$(GIT) -C $(CKAN_PATH) remote update
	$(GIT) -C $(CKAN_PATH) checkout $(CKAN_VERSION)
	$(PIP) install -r $(CKAN_PATH)/requirements.txt
	$(PIP) install -r $(CKAN_PATH)/dev-requirements.txt
	$(PIP) install -e $(CKAN_PATH)
	echo "$(CKAN_VERSION)" > $@

$(SENTINELS)/ckan-installed: $(SENTINELS)/ckan-version | $(SENTINELS)
	@if [ "$(shell cat $(SENTINELS)/ckan-version)" != "$(CKAN_VERSION)" ]; then \
	  echo "Switching to CKAN $(CKAN_VERSION)"; \
	  rm $(SENTINELS)/ckan-version; \
	  $(MAKE) $(SENTINELS)/ckan-version; \
	fi
	@touch $@

$(SENTINELS)/test.ini: $(TEST_INI_PATH) $(CKAN_PATH) $(CKAN_PATH)/test-core.ini | $(SENTINELS)
	$(SED) "s@use = config:.*@use = config:$(CKAN_PATH)/test-core.ini@" -i $(TEST_INI_PATH)
	@touch $@

$(SENTINELS)/requirements: requirements.py$(PYTHON_VERSION).txt dev-requirements.py$(PYTHON_VERSION).txt | $(SENTINELS)
	@touch $@

$(SENTINELS)/install: requirements.py$(PYTHON_VERSION).txt | $(SENTINELS)
	$(PIP) install -r requirements.py$(PYTHON_VERSION).txt
	@touch $@

$(SENTINELS)/install-dev: requirements.py$(PYTHON_VERSION).txt | $(SENTINELS)
	$(PIP) install -r dev-requirements.py$(PYTHON_VERSION).txt
	$(PIP) install -e .
	@touch $@

$(SENTINELS)/develop: $(SENTINELS)/requirements $(SENTINELS)/install $(SENTINELS)/install-dev $(SENTINELS)/test.ini setup.py | $(SENTINELS)
	@touch $@

$(SENTINELS)/dev-setup: $(SENTINELS)/develop
	$(PASTER) --plugin=ckan db init -c $(TEST_INI_PATH)
	@touch $@

$(SENTINELS)/tests-passed: $(SENTINELS)/dev-setup $(shell find $(PACKAGE_DIR) -type f) .flake8 .isort.cfg | $(SENTINELS)
	$(ISORT) -rc -df -c $(PACKAGE_DIR)
	$(FLAKE8) --statistics $(PACKAGE_DIR)
	$(NOSETESTS) --ckan \
	      --with-pylons=$(TEST_INI_PATH) \
          --nologcapture \
          --with-doctest
	@touch $@

# Help related variables and targets

GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)
TARGET_MAX_CHAR_NUM := 15

## Show help
help:
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
	  helpMessage = match(lastLine, /^## (.*)/); \
	  if (helpMessage) { \
	    helpCommand = substr($$1, 0, index($$1, ":")-1); \
	    helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
	    printf "  ${YELLOW}%-$(TARGET_MAX_CHAR_NUM)s${RESET} ${GREEN}%s${RESET}\n", helpCommand, helpMessage; \
	  } \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)
