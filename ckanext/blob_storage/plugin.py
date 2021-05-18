import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.authz_service.authzzie import Authzzie
from ckanext.authz_service.interfaces import IAuthorizationBindings

from . import actions, authz, helpers, validators
from .blueprints import blueprint
from .download_handler import download_handler
from .interfaces import IResourceDownloadHandler


class BlobStoragePlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(IAuthorizationBindings)
    plugins.implements(IResourceDownloadHandler, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IDatasetForm)

    # IDatasetForm
    def create_package_schema(self):
        # let's grab the default schema in our plugin
        schema = super(BlobStoragePlugin, self).create_package_schema()

        schema['resources'].update({
            'url_type': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('upload_has_sha256'),
                toolkit.get_validator('upload_has_size'),
                toolkit.get_validator('upload_has_lfs_prefix')
                ],
            'sha256': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_sha256')
            ],
            'size': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('is_positive_integer'),
            ],
            'lfs_prefix': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_lfs_prefix'),
            ]
        })

        return schema

    def update_package_schema(self):
        schema = super(BlobStoragePlugin, self).update_package_schema()

        schema['resources'].update({
            'url_type': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('upload_has_sha256'),
                toolkit.get_validator('upload_has_size'),
                toolkit.get_validator('upload_has_lfs_prefix')
                ],
            'sha256': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_sha256')
            ],
            'size': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('is_positive_integer'),
            ],
            'lfs_prefix': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_lfs_prefix'),
            ]
        })

        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # IValidators

    def get_validators(self):
        return {
            u'upload_has_sha256': validators.upload_has_sha256,
            u'upload_has_size': validators.upload_has_size,
            u'upload_has_lfs_prefix': validators.upload_has_lfs_prefix,
            u'valid_sha256': validators.valid_sha256,
            u'valid_lfs_prefix': validators.valid_lfs_prefix,
        }

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'blob-storage')

    # ITemplateHelpers

    def get_helpers(self):
        return {'blob_storage_server_url': helpers.server_url,
                'blob_storage_storage_namespace': helpers.storage_namespace}

    # IBlueprint

    def get_blueprint(self):
        return blueprint

    # IActions

    def get_actions(self):
        return {
            'get_resource_download_spec': actions.get_resource_download_spec,
            'resource_schema_show': actions.resource_schema_show,
            'resource_sample_show': actions.resource_sample_show
        }

    # IAuthorizationBindings

    def register_authz_bindings(self, authorizer):
        # type: (Authzzie) -> None
        """Authorization Bindings

        This aliases CKANs Resource entity and actions to scopes understood by
        Giftless' JWT authorization scheme
        """
        # Register object authorization bindings
        authorizer.register_entity_ref_parser('obj', authz.object_id_parser)
        authorizer.register_authorizer('obj', authz.check_object_permissions,
                                       actions={'update', 'read'},
                                       subscopes=(None, 'data', 'metadata'))
        authorizer.register_action_alias('write', 'update', 'obj')
        authorizer.register_scope_normalizer('obj', authz.normalize_object_scope)

    # IResourceDownloadHandler

    def resource_download(self, resource, package, filename=None, inline=False, activity_id=None):
        return download_handler(resource, package, filename, inline, activity_id)
