"""Authorization related helpers
"""
import logging
from typing import Optional, Set

from ckan.plugins import toolkit

from ckanext.authz_service.authz_binding import resource as res_authz
from ckanext.authz_service.authz_binding.common import get_user_context
from ckanext.authz_service.authzzie import Scope

log = logging.getLogger(__name__)


def normalize_object_scope(_, granted_scope):
    # type: (Scope, Scope) -> Scope
    """Normalize resource scope by trimming out the org/dataset part and only leaving the sha256

    This helps us deal with cases where a resource is moved (i.e. the dataset is renamed, or the
    organization is renamed, or the dataset is moved to a different organization)
    """
    if not granted_scope:
        return granted_scope

    entity_ref_parts = granted_scope.entity_ref.split('/')
    if entity_ref_parts[-1] in {'*', ''} or len(entity_ref_parts) < 3:
        return granted_scope

    return Scope(granted_scope.entity_type, entity_ref_parts[-1], granted_scope.actions, granted_scope.subscope)


def check_resource_permissions(id, dataset_id=None, organization_id=None):
    # type: (str, Optional[str], Optional[str]) -> Set[str]
    """Check resource read permissions, allowing sha256 to be specified instead of resource ID
    """
    if not _is_sha256_hex(id):
        log.debug("Given object id [%s] is not a sha256, falling back to default authorizer", id)
        return res_authz.check_resource_permissions(id, dataset_id, organization_id)

    log.debug("Given object id [%s] looks like sha256, checking resources for a match", id)
    ds_permissions = res_authz.check_resource_permissions(None, dataset_id, organization_id)
    if len(ds_permissions) > 0 and _has_resource_with_sha256(dataset_id, id):
        return ds_permissions

    return set()


def _has_resource_with_sha256(dataset_id, sha256):
    # type: (str, str) -> bool
    """Check that there's a resource in the dataset with sha256 set to the provided value
    """
    try:
        dataset = toolkit.get_action('package_show')(get_user_context(), {'id': dataset_id})
        for res in dataset['resources']:
            if res.get('sha256') == sha256:
                return True
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        pass

    return False


def _is_sha256_hex(value):
    # type: (str) -> bool
    """Check if a string is a valid sha256 hex

    >>> _is_sha256_hex('853ff93762a06ddbf722c4ebe9ddd66d8f63ddaea97f521c3ecc20da7c976020')
    True

    >>> _is_sha256_hex('0x3ff93762a06ddbf722c4ebe9ddd66d8f63ddaea97f521c3ecc20da7c976020')
    False

    >>> _is_sha256_hex('some random string')
    False

    >>> _is_sha256_hex('cd50d19784897085a8d0e3e413f8612b097c03f1')
    False
    """
    if len(value) != 64 or value[1] in {'x', 'X'}:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True
