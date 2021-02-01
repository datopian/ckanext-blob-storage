from ckanext.external_storage import validators


def test_upload_has_sha256():
    key = ('resources', 0, 'url_type')
    flattened_data = {
        (u'resources', 0, u'url_type'): u'upload',
        (u'resources', 0, u'url'): u'/my/file.csv',
        (u'resources', 0, u'__extras'): {'sha256': u'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919'}
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
