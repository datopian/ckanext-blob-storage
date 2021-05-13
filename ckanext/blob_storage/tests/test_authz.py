import pytest
from ckan.tests import factories, helpers

from ckanext.authz_service.authzzie import Scope
from ckanext.blob_storage import authz
from ckanext.blob_storage.tests import user_context


def test_normalize_object_scope():
    scope = Scope('foo', 'bar', {'read'})
    normalized_scope = authz.normalize_object_scope(None, scope)
    assert 'foo:bar:read' == str(normalized_scope)


@pytest.mark.usefixtures('clean_db', 'reset_db', 'with_request_context')
def test_normalize_object_scope_with_lfs():
    org = factories.Organization()
    dataset = factories.Dataset(owner_org=org['id'])
    resource = factories.Resource(
        url='/my/file.csv',
        url_type='upload',
        sha256='cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
        size=123456,
        lfs_prefix='lfs_prefix',
        package_id=dataset['id']
    )

    scope_str = 'obj:{}/{}/{}:read'.format(org['name'], dataset['name'], resource['id'])
    scope = Scope.from_string(scope_str)

    normalized_scope = authz.normalize_object_scope(None, scope)

    expected_scpope = 'obj:{}/{}:read'.format(
        resource['lfs_prefix'],
        resource['sha256']
    )
    assert expected_scpope == str(normalized_scope)


@pytest.mark.usefixtures('clean_db', 'reset_db', 'with_request_context')
def test_normalize_object_scope_with_activity_id():
    sysadmin = factories.Sysadmin()
    org = factories.Organization()
    dataset = factories.Dataset(owner_org=org['id'])
    resource = factories.Resource(
        url='/my/file.csv',
        url_type='upload',
        sha256='cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
        size=123456,
        lfs_prefix='lfs_prefix',
        package_id=dataset['id']
    )
    resource_2 = helpers.call_action(
        'resource_patch',
        id=resource['id'],
        url='/my/file-2.csv',
        sha256='dd71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
        size=2345678,
    )

    # Building scope without activity_id
    scope_str = 'obj:{}/{}/{}:read'.format(org['name'], dataset['name'], resource['id'])
    scope = Scope.from_string(scope_str)

    normalized_scope = authz.normalize_object_scope(None, scope)

    # Expected scope should have the current lfs metadata (lfs_prefix and sha256)
    expected_scope = 'obj:{}/{}:read'.format(
        resource_2['lfs_prefix'],
        resource_2['sha256']
    )
    assert expected_scope == str(normalized_scope)

    # Editing the resource so the latest version is different from resource_2
    helpers.call_action(
        'resource_patch',
        id=resource['id'],
        url='/my/file-3.csv',
        sha256='ee71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
        size=3456789,
    )

    resource_2_activity_id = helpers.call_action(
        'package_activity_list',
        id=dataset['id']
        )[-1]['id']

    # Building scope with activity_id of resource_2
    scope_str = 'obj:{}/{}/{}/{}:read'.format(
        org['name'],
        dataset['name'],
        resource['id'],
        resource_2_activity_id
        )
    scope = Scope.from_string(scope_str)

    with user_context(sysadmin):
        normalized_scope = authz.normalize_object_scope(None, scope)

    assert expected_scope == str(normalized_scope)
