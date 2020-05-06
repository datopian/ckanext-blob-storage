"""Template helpers for ckanext-external-storage
"""
from typing import Optional

import ckan.plugins.toolkit as toolkit


def resource_storage_prefix(package_name, org_name=None):
    # type: (str) -> str
    """Get the resource storage prefix for a package name
    """
    if org_name is None:
        try:
            context = {'ignore_auth': True}
            data_dict = {'id': package_name}
            package = toolkit.get_action('package_show')(context, data_dict)
        except toolkit.ObjectNotFound:
            return ''

        org_name = package.get('organization', {}).get('name')
        if not org_name:
            org = package.get('owner_org', {})
            org_name = org.get('name')

    if not org_name:
        org_name = '_'

    return '{}/{}'.format(org_name, package_name)


def resource_authz_scope(package_name, actions=None, org_name=None):
    # type: (str, Optional[str]) -> str
    """Get the authorization scope for package resources
    """
    if actions is None:
        actions = 'read,write'
    return 'obj:{}/*:{}'.format(resource_storage_prefix(package_name, org_name), actions)


def server_url():
    # type: () -> Optional[str]
    """Get the configured server URL
    """
    return toolkit.config.get('ckanext.external_storage.storage_service_url')
