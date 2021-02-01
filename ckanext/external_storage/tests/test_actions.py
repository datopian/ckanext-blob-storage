import ckan.plugins.toolkit as toolkit
import pytest
from ckan.tests import factories


@pytest.mark.usefixtures("clean_db")
def test_validation_error_if_not_sha256():
    with pytest.raises(toolkit.ValidationError):
        factories.Dataset(
            resources=[
                {'url': '/my/file.csv', 'url_type': 'upload', 'size': 12345}
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
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919'
                }
            ]
        )


@pytest.mark.usefixtures("clean_db")
def test_no_validation_error_if_not_upload():
    factories.Dataset(
            resources=[{'url': 'https://www.example.com', 'url_type': ''}]
        )


@pytest.mark.usefixtures("clean_db")
def test_no_validation_error_if_sha256_and_size_are_set():
    factories.Dataset(
            resources=[
                {
                    'url': '/my/file.csv',
                    'url_type': 'upload',
                    'sha256': 'cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919',
                    'size': 12345
                }
            ]
        )
