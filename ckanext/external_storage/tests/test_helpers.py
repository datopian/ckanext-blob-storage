import pytest

from ckanext.external_storage import helpers


# @pytest.mark.usefixtures('ckan_config')
@pytest.mark.ckan_config('ckanext.external_storage.storage_service_url', 'https://foo.example.com/lfs')
def test_server_url_from_config():
    assert 'https://foo.example.com/lfs' == helpers.server_url()


# @pytest.mark.usefixtures('ckan_config')
@pytest.mark.ckan_config('ckanext.external_storage.storage_service_url', 'https://foo.example.com/lfs/')
def test_server_url_strip_trailing_slash():
    assert 'https://foo.example.com/lfs' == helpers.server_url()
