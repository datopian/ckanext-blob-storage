ckanext-external-storage
========================
[![Build Status](https://travis-ci.org/datopian/ckanext-external-storage.svg?branch=master)](https://travis-ci.org/datopian/ckanext-external-storage)
[![Coverage Status](https://coveralls.io/repos/github/datopian/ckanext-external-storage/badge.svg?branch=master)](https://coveralls.io/github/datopian/ckanext-external-storage?branch=master)

**Move CKAN resource storage management to an external micro-service**

`ckanext-external-storage` replace's CKAN's data storage functionality 
with an external micro-service deployed separately of CKAN. This stand-alone
micro-service is responsible for authorizing access to storage backends,
which could in turn be local, cloud based (e.g. S3, Azure Blobs, GCP, etc.)
or any other storage. In addition, the service allows clients (typically
browsers) to upload and download files directly to storage without passing
them through CKAN, which can greatly improve file access efficiency.

Authentication and authorization to the external storage management service
is done via JWT tokens provided by 
[`ckanext-authz-service`](https://github.com/datopian/ckanext-authz-service).

Internally, the external storage management service is in fact a Git LFS server
implementation, which means access via 3rd party Git based tools is also 
potentially possible. 

Requirements
------------
* This extension works with CKAN 2.8.x. It may work, but has not been tested, 
with other CKAN versions.
* `ckanext-authz-service` must be installed and enabled
* A working and configured Git LFS server accessible to the browser. We 
recommend usign [Giftless](https://github.com/datopian/giftless) but other 
implementations may be configured to work as well.

Installation
------------

To install ckanext-external-storage:

1. Activate your CKAN virtual environment, for example:
```
. /usr/lib/ckan/default/bin/activate
```

2. Install the ckanext-external-storage Python package into your virtual environment:
```
pip install ckanext-external-storage
```

3. Add `external_storage` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/production.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:
```
sudo service apache2 reload
```

Configuration settings
----------------------

`ckanext.external_storage.storage_service_url = 'https://...'`

Set the URL of the external storage microservice (the Git LFS server). This
must be a URL accessible to browsers connecting to the service. 


Developer installation
----------------------

To install `ckanext-external-storage` for development, do the following:

1. Pull the project code from Github
```
git clone https://github.com/datopian/ckanext-external-storage.git 
cd ckanext-external-storage 
```
2. Create a Python 2.7 virtual environment
```
virtualenv .venv27
source .venv27/bin/activate
```

3. Install the dependencies
```
npm install
```

4. Generate the [ckan3-js-sdk](https://github.com/datopian/ckan3-js-sdk) bundle
```
npm run build
```

5. Run the following command to bootstrap the entire environment
```
make dev-start
```

This will pull and install CKAN and all it's dependencies into your virtual
environment, create all necessary configuration files, launch external services
using Docker Compose and start the CKAN development server.

You can repeat the last command at any time to start developing again. 

Type `make help` to get a like of user commands useful to managing the local
environment. 


### Working with `requirements.txt` files

#### tl;dr

* You *do not* touch `*requirements.*.txt` files directly. We use 
[`pip-tools`][1] and custom `make` targets to manage these files. 
* Use `make develop` to install the right development time requirements into your 
current virtual environment
* Use `make install` to install the right runtime requirements into your current
virtual environment
* To add requirements, edit `requirements.in` or `dev-requirements.in` and run
`make requirements`. This will recompile the requirements file(s) **for your 
current Python version**. You may need to do this for the other Python version
by switching to a different Python virtual environment before committing your 
changes. 
 
#### More background
This project manages requirements in a relatively complex way, in order to 
seamlessly support Python 2.7 and 3.x.

For this reason, you will see 4 requirements files in the project root:

* `requirements.py2.txt` - Python 2 runtime requirements 
* `requirements.py3.txt` - Python 3 runtime requirements 
* `dev-requirements.py2.txt` - Python 2 development requirements
* `dev-requirements.py3.txt` - Python 3 development requirements

These are generated using the `pip-compile` command (a part of `pip-tools`)
from the corresponding `requirements.in` and `dev-requirements.in` files. 

To understand why `pip-compile` is used, read the `pip-tools` manual. In 
short, this allows us to pin dependencies of dependencies, thus resolving 
potential deployment conflicts, without the headache of managing the specific
version of each Nth-level dependency. 

In order to support both Python 2.7 and 3.x, which tend to require slightly
different dependencies, we use `requirements.in` files to generate 
major-version specific requirements files. These, in turn, should be used
when installing the package. 

In order to simplify things, the `make` targets specified above will automate
the process *for the current Python version*. 

#### Adding Requirements

Requirements are managed in `.in` files - these are the only files that
should be edited directly. 

Take care to specify a version for each requirement, to the level required
to maintain future compatibility, but not to specify an *exact* version 
unless necessary. 

For example, the following are good `requirements.in` lines:

    pyjwt[crypto]==1.7.*
    pyyaml==5.*
    pytz
    
This allows these packages to be upgraded to a minor version, without the risk
of breaking compatibility. 

Note that `pytz` is specified with no version on purpose, as we want it updated
to the latest possible version on each new rebuild. 

Developers wanting to add new requirements (runtime or development time),
should take special care to update the `requirements.txt` files for all
supported Python versions by running `make requirements` on different
virtual environment, after updating the relevant `.in` file. 

#### Applying Patch-level upgrades to requirements

You can delete `*requirements.*.txt` and run `make requirements`. 

TODO: we can probably do this in a better way - create a `make` target
for this.  


Tests
-----

To run the tests, do:

    make test

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run:

    make coverage

Releasing a new version of ckanext-external-storage
------------------------------------------------

ckanext-external-storage should be available on PyPI as https://pypi.org/project/ckanext-external-storage.
To publish a new version to PyPI follow these steps:

1. Update the version number in the `setup.py` file.
   See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) 
   for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:
```
    pip install --upgrade setuptools wheel twine
```

3. Create a source and binary distributions of the new version:
```
    python setup.py sdist bdist_wheel && twine check dist/*
```

   Fix any errors you get.

4. Upload the source distribution to PyPI:
```
    twine upload dist/*
```

5. Commit any outstanding changes:
```
    git commit -a
```

6. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do:
```
    git tag 0.0.1
    git push --tags
```


[1]: https://pypi.org/project/pip-tools/
