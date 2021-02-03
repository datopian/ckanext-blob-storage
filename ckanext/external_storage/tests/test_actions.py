import ckan.plugins.toolkit as toolkit
import pytest
from ckan.tests import factories


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_not_sha256():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'size': 12345,
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_not_size_on_uploads():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_not_lfs_prefix_on_uploads():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': 123456
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_no_validation_error_if_not_upload():
    factories.Dataset(
            resources=[{'url': 'https://www.example.com', 'url_type': ''}]
        )


@pytest.mark.usefixtures("clean_db")
def test_no_validation_error_if_all_fields_are_set():
    dataset = factories.Dataset(
        resources=[
            {
                'url': '/my/file.csv',
                'url_type': 'upload',
                'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                'size': 12345,
                'lfs_prefix': 'lfs/prefix'
            }
        ]
    )

    assert dataset['resources'][0]['sha256'] == 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919'
    assert dataset['resources'][0]['size'] == 12345
    assert dataset['resources'][0]['lfs_prefix'] == 'lfs/prefix'


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_wrong_sha256():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'wrong_sha256',
                    'size': 123456,
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_size_not_positive_integer():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': -12,
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )

    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': 0,
                    'lfs_prefix': 'lfs/prefix'
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_empty_lfs_prefix():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': 123456,
                    'lfs_prefix': ''
                }
            ]
        )
