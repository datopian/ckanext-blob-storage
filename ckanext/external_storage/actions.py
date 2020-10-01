"""External Storage API actions
"""
import ast
from os import path
from typing import Any, Dict

from ckan.plugins import toolkit
from six.moves.urllib.parse import urlparse

from . import helpers
from .lfs_client import LfsClient, LfsError


@toolkit.side_effect_free
def get_resource_download_spec(context, data_dict):
    """Get a signed URL from LFS server to download a resource
    """
    resource = _get_resource(context, data_dict)
    for k in ('lfs_prefix', 'sha256', 'size'):
        if k not in resource:
            return {}

    client = get_lfs_client(context, resource)
    object = _get_resource_download_lfs_objects(client, resource['lfs_prefix'], [resource])[0]
    assert object['oid'] == resource['sha256']
    assert object['size'] == resource['size']

    if 'error' in object:
        raise toolkit.ObjectNotFound('Object error [{}]: {}'.format(object['error'].get('message', '[no message]'),
                                                                    object['error'].get('code', 'unknown')))

    return object['actions']['download']


@toolkit.side_effect_free
def resource_schema_show(context, data_dict):
    """Get a resource schema as a dictionary instead of string
    """
    resource = _get_resource(context, data_dict)

    if resource.get('schema', False):
        try:
            return ast.literal_eval(resource['schema'])
        except ValueError:
            return resource['schema']
    return {}


@toolkit.side_effect_free
def resource_sample_show(context, data_dict):
    """Get a resource sample as a list of dictionaries instead of string
    """
    resource = _get_resource(context, data_dict)

    if resource.get('sample', False):
        try:
            return ast.literal_eval(resource['sample'])
        except ValueError:
            return resource['sample']
    return {}


def get_lfs_client(context, resource):
    """Get an LFS client object; This is a poor man's DI solution
    that allows injecting an LFS client object via the CKAN context
    """
    return context.get('lfs_client', LfsClient(helpers.server_url(), _get_authz_token(context, resource)))


def _get_resource_download_lfs_objects(client, lfs_prefix, resources):
    """Get LFS download operation response objects for a given resource list
    """
    objects = [{"oid": r['sha256'],
                "size": r['size'],
                "x-filename": _get_filename(r)} for r in resources]
    try:
        batch_response = client.batch(lfs_prefix, 'download', objects)
    except LfsError as e:
        if e.status_code == 404:
            raise toolkit.ObjectNotFound("The requested resource does not exist")
        elif e.status_code == 422:
            raise toolkit.ObjectNotFound("Object parameters mismatch")
        elif e.status_code == 403:
            raise toolkit.NotAuthorized("You are not authorized to download this resource")
        else:
            raise

    return batch_response['objects']


def _get_authz_token(context, resource):
    # type: (Dict[str, Any], Dict[str, Any]) -> str
    """Get an authorization token for getting the URL from LFS
    """
    authorize = toolkit.get_action('authz_authorize')
    if not authorize:
        raise RuntimeError("Cannot find authz_authorize; Is ckanext-authz-service installed?")

    org_name, package_name = resource['lfs_prefix'].split('/')
    scope = helpers.resource_authz_scope(package_name, org_name=org_name, actions='read')
    authz_result = authorize(context, {"scopes": [scope]})

    if not authz_result or not authz_result.get('token', False):
        raise RuntimeError("Failed to get authorization token for LFS server")

    if len(authz_result['granted_scopes']) == 0:
        raise toolkit.NotAuthorized("You are not authorized to download this resource")

    return authz_result['token']


def _get_resource(context, data_dict):
    """Get resource by ID
    """
    if 'resource' in data_dict:
        return data_dict['resource']
    return toolkit.get_action('resource_show')(context, {'id': data_dict['id']})


def _get_filename(resource):
    """Get original file name from resource
    """
    if 'url' not in resource:
        return resource['name']

    if resource['url'][0:6] in {'http:/', 'https:'}:
        url_path = urlparse(resource['url']).path
        return path.basename(url_path)
    return resource['url']
