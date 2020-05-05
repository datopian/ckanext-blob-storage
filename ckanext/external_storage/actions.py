"""External Storage API actions
"""
from ckan.plugins import toolkit

from . import helpers
from .lfs_client import LfsClient, LfsError


@toolkit.side_effect_free
def get_resource_download_spec(context, data_dict):
    """Get a signed URL from LFS server to download a resource
    """
    if 'resource' in data_dict:
        resource = data_dict['resource']
    else:
        resource = _get_resource(context, data_dict.get['id'])

    for k in ('lfs_prefix', 'sha256', 'size'):
        if k not in resource:
            return {}

    org_name, package_name = resource['lfs_prefix'].split('/')

    authorize = toolkit.get_action('authz_authorize')
    if not authorize:
        raise RuntimeError("Cannot find authz_authorize; Is ckanext-authz-service installed?")

    scope = helpers.resource_authz_scope(package_name, org_name=org_name, actions='read')
    authz_result = authorize(context, {"scopes": [scope]})

    if not authz_result or not authz_result.get('token', False):
        raise RuntimeError("Failed to get authorization token for LFS server")

    if len(authz_result['granted_scopes']) == 0:
        raise toolkit.NotAuthorized("You are not authorized to download this resource")

    client = LfsClient(helpers.server_url(), authz_result['token'])
    object = {"oid": resource['sha256'], "size": resource['size']}

    try:
        batch_response = client.batch(resource['lfs_prefix'], 'download', [object])
    except LfsError as e:
        if e.status_code == 404:
            raise toolkit.ObjectNotFound("The requested resource does not exist")
        elif e.status_code == 422:
            raise toolkit.ObjectNotFound("Object parameters mismatch")
        elif e.status_code == 403:
            raise toolkit.NotAuthorized("You are not authorized to download this resource")
        else:
            raise

    object = batch_response['objects'][0]
    assert object['oid'] == resource['sha256']
    assert object['size'] == resource['size']

    if 'error' in object:
        raise toolkit.ObjectNotFound('Object error [{}]: {}'.format(object['error'].get('message', '[no message]'),
                                                                    object['error'].get('code', 'unknown')))

    return object['actions']['download']


def _get_resource(context, resource_id):
    """Get resource by ID
    """
    return toolkit.get_action('resource_show')(context, {'id': resource_id})


def _get_package(context, package_id):
    """Get package by ID
    """
    return toolkit.get_action('package_show')(context, {'id': package_id})
