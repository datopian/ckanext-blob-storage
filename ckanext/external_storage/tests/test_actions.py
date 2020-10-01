from ckan.tests import factories
from ckan.tests import helpers as test_helpers

from ckanext.external_storage.tests import get_context


class TestBlobSotrageActions():
    """Test cases for logic actions
    """

    org_admin = factories.User()
    initial_dataset = factories.Dataset()

    first_resource = factories.Resource(
        name="First Resource",
        package_id=initial_dataset['id'],
        sample="{u'1': {u'VMP_SNOMED_CODE': u'4747111000001104', u'ODS_CODE': u'REF'}}",
        schema="{u'fields': [{u'type': u'string'}], u'missingValues': [u'']}"
    )

    second_resource = factories.Resource(
        name="First Resource",
        package_id=initial_dataset['id'],
        sample={'1': {'VMP_SNOMED_CODE': '4747111000001104'}},
        schema={'fields': [{'type': 'string'}], 'missingValues': ['']}
    )

    def test_resource_schema_show(self):
        """Test if the resource.schema is a string the resource_sample_show should return JSON object
        """
        context = get_context(self.org_admin)
        expect = {'fields': [{'type': 'string'}], 'missingValues': ['']}

        resource_schema = test_helpers.call_action(
            'resource_schema_show',
            context,
            id=self.first_resource['id'])

        assert resource_schema == expect

    def test_resource_sample_show(self):
        """Test if the resource.sample is a string the resource_sample_show should return JSON object
        """
        context = get_context(self.org_admin)
        expect = {'1': {'VMP_SNOMED_CODE': '4747111000001104', 'ODS_CODE': 'REF'}}

        resource_sample = test_helpers.call_action(
            'resource_sample_show',
            context,
            id=self.first_resource['id'])

        assert resource_sample == expect

    def test_resource_schema_show_and_resource_sample_show_with_new_ckan_version(self):
        """Test with CKAN version >=2.8.5 should not be broken if is already a JSON object
        """
        context = get_context(self.org_admin)
        expect_sample = {'1': {'VMP_SNOMED_CODE': '4747111000001104'}}
        expect_schema = {'fields': [{'type': 'string'}], 'missingValues': ['']}

        resource_sample = test_helpers.call_action(
            'resource_sample_show',
            context,
            id=self.second_resource['id'])

        resource_schema = test_helpers.call_action(
            'resource_schema_show',
            context,
            id=self.second_resource['id'])

        assert resource_sample == expect_sample
        assert resource_schema == expect_schema
