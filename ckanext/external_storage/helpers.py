"""Template helpers for ckanext-external-storage
"""
from typing import Optional

import ckan.plugins.toolkit as toolkit


def resource_storage_prefix(package_name):
    # type: (str) -> str
    """Get the resource storage prefix for a package name
    """
    try:
        context = {'ignore_auth': True}
        data_dict = {'id': package_name}
        package = toolkit.get_action('package_show')(context, data_dict)
    except toolkit.ObjectNotFound:
        return ''

    org = package.get('organization', {}).get('name')
    if not org:
        org = package.get('owner_org')
    if not org:
        org = '_'

    return '{}/{}'.format(org, package_name)


def resource_authz_scope(package_name, actions=None):
    # type: (str, Optional[str]) -> str
    """Get the authorization scope for package resources
    """
    if actions is None:
        actions = 'read,write'
    return 'obj:{}/*:{}'.format(resource_storage_prefix(package_name), actions)


def server_url():
    return 'http://127.0.0.1:9419'
