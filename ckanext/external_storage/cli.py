import errno
import hashlib
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Generator, Union

import requests
from ckan.model import Session, Resource
from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit
from flask import Response
from six import string_types, binary_type
from sqlalchemy.orm.attributes import flag_modified

from ckanext.external_storage import helpers
from ckanext.external_storage.download_handler import call_download_handlers

log = logging.getLogger(__name__)


class MigrateResourcesCommand(CkanCommand):
    """Migrate all non-migrated resources to external blob storage
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0

    def command(self):
        self._load_config()
        self._migrate_all_resources()

    @staticmethod
    def _migrate_all_resources():
        """Do the actual migration
        """
        migrated = 0
        for resource_obj in get_unmigrated_resources():
            log.info("Starting to migrate resource %s", resource_obj.id)
            package = get_resource_package(resource_obj)
            with download_resource(resource_obj, package) as resource_file:
                props = get_resource_lfs_props(package, resource_file)
                log.debug("Calculated additional LFS properties: %s", props)
                upload_resource(resource_file, props)
            update_storage_props(resource_obj, props)
            log.info("Finished migrating resource %s", resource_obj.id)
            migrated += 1

        log.info("Finished migrating %d resources", migrated)


def get_resource_lfs_props(package, resource_file):
    # type: (Dict[str, Any], str) -> Dict[str, Union[str, int]]
    """Get some key LFS attributes for a resource / file
    """
    org_name = helpers.organization_name_for_package(package)
    log.debug("Calculating SHA-256 for %s ... ")
    with open(resource_file, 'rb') as f:
        sha256 = hashlib.sha256(f)

    return {'lfs_prefix': helpers.resource_storage_prefix(package['name'], org_name),
            'sha256': sha256.hexdigest(),
            'size': os.path.getsize(resource_file)}


def upload_resource(resource_file, lfs_props):
    """Upload a resource file to new storage using LFS server
    """
    token = get_upload_authz_token(lfs_props['lfs_prefix'])
    # Get an instance of the LFS client
    # Send batch request
    # Upload file


def update_storage_props(resource, lfs_props):
    # type: (Resource, Dict[str, Any]) -> None
    """Update the resource with new storage properties
    """
    resource.extras['lfs_prefix'] = lfs_props['lfs_prefix']
    resource.extras['sha256'] = lfs_props['sha256']
    resource.size = lfs_props['size']
    flag_modified(resource, 'extras')


@contextmanager
def download_resource(resource, package):
    # type: (Dict[str, Any], Dict[str, Any]) -> str
    """Download the resource to a local file and provide the file name

    This is a context manager that will delete the local file once context is closed
    """
    resource_file = tempfile.mktemp(prefix='ckan-blob-migration-')
    try:
        # Need resource and package dicts
        response = call_download_handlers(resource, package)
        if response.status_code == 200:
            _save_downloaded_response_data(response, resource_file)
        elif response.status_code in {301, 302}:
            _save_redirected_response_data(response, resource_file)
        else:
            raise RuntimeError("Unexpected download response code: {}".format(response.status_code))
        yield resource_file
    finally:
        try:
            os.unlink(resource_file)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


def _save_downloaded_response_data(response, file_name):
    # type: (Response, str) -> None
    """Get an HTTP response object with open file containing a resource and save the data locally
    to a temporary file
    """
    with open(file_name, 'wb') as f:
        if isinstance(response.response, (string_types, binary_type)):
            log.debug("Response contains inline string data, saving to %s", file_name)
            f.write(response.response)
        elif hasattr(response.response, 'read'):  # assume an open stream / file
            log.debug("Response contains an open file object, copying to %s", file_name)
            shutil.copyfileobj(response.response, f)
        else:
            raise ValueError("Don't know how to handle response type: {}".format(type(response.response)))


def _save_redirected_response_data(response, file_name):
    # type: (Response, str) -> None
    """Download the URL of a remote resource we got redirected to, and save it locally

    Return the local file name
    """
    resource_url = response.headers['Location']
    log.debug("Resource is at %s, downloading ...", resource_url)
    with requests.get(resource_url, stream=True) as source, open(file_name, 'wb') as dest:
        source.raise_for_status()
        log.debug("Resource downloading, HTTP status code is %d, Content-type is %s",
                  source.status_code,
                  source.headers.get('Content-type', 'unknown'))
        for chunk in source.iter_content(chunk_size=1024 * 16):
            dest.write(chunk)
    log.debug("Remote resource downloaded to %s", file_name)


def get_resource_package(resource_obj):
    # type: (Resource) -> Dict[str, Any]
    """Fetch the CKAN package dictionary for a DB-fetched resource
    """
    package = toolkit.get_action('package_read')({"id": resource_obj.package_id},
                                                 {"ignore_auth": True})
    return package


def get_upload_authz_token(lfs_prefix):
    # type: (str) -> str
    """Get an authorization token to upload the file to LFS
    """
    authorize = toolkit.get_action('authz_authorize')
    if not authorize:
        raise RuntimeError("Cannot find authz_authorize; Is ckanext-authz-service installed?")

    context = {'ignore_auth': True}
    package_name, org_name = lfs_prefix.split('/')
    scope = helpers.resource_authz_scope(package_name, org_name=org_name, actions='write')
    authz_result = authorize(context, {"scopes": [scope]})

    if not authz_result or not authz_result.get('token', False):
        raise RuntimeError("Failed to get authorization token for LFS server")

    if len(authz_result['granted_scopes']) == 0:
        raise toolkit.NotAuthorized("You are not authorized to upload resources")

    return authz_result['token']


def get_unmigrated_resources():
    # type: () -> Generator[Resource, None, None]
    """Generator of un-migrated resource

    This works by fetching one resource at a time using SELECT FOR UPDATE SKIP LOCKED.
    Once the resource has been migrated to the new storage, it will be unlocked. This
    allows running multiple migrator scripts in parallel, without any conflicts and
    with small chance of re-doing any work.

    While a specific resource is being migrated, it will be locked for modification
    on the DB level. Users can still read the resource without any effect.
    """
    resources = Session.query(Resource).filter(Resource.url_type == 'upload',
                                               Resource.extras.not_like('%"lfs_prefix":%'))
    log.info("There are ~%d resources left to migrate", resources.count())
    while True:
        with Session.begin():
            resource = resources.for_update(skip_locked=True).one_or_none()
            if resource is None:
                break  # We are done here

            # let's double check as the LIKE selection is not the safest
            if _was_migrated(resource):
                continue

            yield resource


def _was_migrated(resource):
    # type: (Resource) -> bool
    """Check the attributes of a resource to see if it was migrated
    """
    return resource.extras.get('lfs_prefix') and resource.extras.get('sha256')
