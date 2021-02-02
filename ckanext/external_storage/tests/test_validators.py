import pytest
from ckan.plugins.toolkit import Invalid

from ckanext.external_storage import validators


def test_upload_has_sha256():
    key = ('resources', 0, 'url_type')
    flattened_data = {
        (u'resources', 0, u'url_type'): u'upload',
        (u'resources', 0, u'url'): u'/my/file.csv',
        (u'resources', 0, u'sha256'): u'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919'
    }
    validators.upload_has_sha256(key, flattened_data, {}, {})

    with pytest.raises(Invalid):
        flattened_data = {
            (u'resources', 0, u'url_type'): u'upload',
            (u'resources', 0, u'url'): u'/my/file.csv',
        }
        validators.upload_has_sha256(key, flattened_data, {}, {})


def test_upload_has_size():
    key = ('resources', 0, 'url_type')
    flattened_data = {
        (u'resources', 0, u'url_type'): u'upload',
        (u'resources', 0, u'url'): u'/my/file.csv',
        (u'resources', 0, u'size'): 123456
    }
    validators.upload_has_size(key, flattened_data, {}, {})

    with pytest.raises(Invalid):
        flattened_data = {
            (u'resources', 0, u'url_type'): u'upload',
            (u'resources', 0, u'url'): u'/my/file.csv',
        }
        validators.upload_has_size(key, flattened_data, {}, {})


def test_upload_has_lfs_prefix():
    key = ('resources', 0, 'url_type')
    flattened_data = {
        (u'resources', 0, u'url_type'): u'upload',
        (u'resources', 0, u'url'): u'/my/file.csv',
        (u'resources', 0, u'__extras'): {'lfs_prefix': u'lfs/prefix'}
    }
    validators.upload_has_lfs_prefix(key, flattened_data, {}, {})

    with pytest.raises(Invalid):
        flattened_data = {
            (u'resources', 0, u'url_type'): u'upload',
            (u'resources', 0, u'url'): u'/my/file.csv'
        }
        validators.upload_has_lfs_prefix(key, flattened_data, {}, {})


def test_valid_sha256():
    validators.valid_sha256('cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919')

    with pytest.raises(Invalid):
        validators.valid_sha256('wrong_sha256')


def test_sha256_doesnt_raise_if_not_upload():
    key = ('resources', 0, 'url_type')
    flattened_data = {
        (u'resources', 0, u'url_type'): u'',
        (u'resources', 0, u'url'): u'https://www.google.com',
    }
    validators.upload_has_sha256(key, flattened_data, {}, {})


def test_size_doesnt_raise_if_not_upload():
    key = ('resources', 0, 'url_type')
    flattened_data = {
        (u'resources', 0, u'url_type'): u'',
        (u'resources', 0, u'url'): u'https://www.google.com',
    }
    validators.upload_has_size(key, flattened_data, {}, {})


def test_lfs_prefix_doesnt_raise_if_not_upload():
    key = ('resources', 0, 'url_type')
    flattened_data = {
        (u'resources', 0, u'url_type'): u'',
        (u'resources', 0, u'url'): u'https://www.google.com',
    }
    validators.upload_has_lfs_prefix(key, flattened_data, {}, {})
