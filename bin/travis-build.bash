#!/bin/bash
set -e

echo "This is travis-build.bash..."
echo "Targetting CKAN $CKANVERSION on Python $TRAVIS_PYTHON_VERSION"

make ckan-install CKAN_VERSION=$CKANVERSION

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan WITH PASSWORD 'ckan';"
sudo -u postgres psql -c "CREATE USER datastore_ro WITH PASSWORD 'datastore_ro';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan;'
sudo -u postgres psql -c 'CREATE DATABASE datastore_test WITH OWNER ckan;'

echo "travis-build.bash is done."
