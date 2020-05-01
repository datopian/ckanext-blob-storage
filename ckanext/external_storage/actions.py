"""External Storage API actions
"""
from ckan.plugins import toolkit

from . import helpers
from .lfs_client import LfsClient, LfsError


@toolkit.sideeffect_free
def extstorage_get_resource_url(context, data_dict):
    """Get a signed URL from LFS server to download a resource
    """
    if 'resource' in data_dict:
        resource = data_dict['resource']
    else:
        resource = get_resource(data_dict.get['id'])

    for k in ('lfs_prefix', 'sha256', 'size'):
        if k not in resource:
            return {}

    if 'package_name' in data_dict:
        package_name = data_dict['package_name']
    else:
        package_name = get_package(resource['package_id'])['name']

    org_name = resource['organization']['name']

    authorize = toolkit.get_action('authz_authorize')
    if not authorize:
        raise RuntimeError("Cannot find authz_authorize; Is ckanext-authz-service installed?")

    scope = helpers.resource_authz_scope(package_name, org_name=org_name, actions='read')
    authz_result = authorize(context, {"scopes": [scope]})

    if not authz_result or not authz_result.get('success', False):
        raise RuntimeError("Failed to get authorization token for LFS server")

    if len(authz_result['data']['granted_scopes']) == 0:
        raise toolkit.NotAuthorized("You are not authorized to download this resource")

    client = LfsClient(helpers.server_url(), authz_result['data']['token'])
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
