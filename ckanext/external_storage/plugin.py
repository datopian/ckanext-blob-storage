import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.authz_service.interfaces import IAuthorizationBindings

from . import actions, helpers
from .blueprints import blueprint


class ExternalStoragePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(IAuthorizationBindings)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'external-storage')

    # ITemplateHelpers

    def get_helpers(self):
        return {'extstorage_server_url': helpers.server_url,
                'extstorage_resource_authz_scope': helpers.resource_authz_scope,
                'extstorage_resource_storage_prefix': helpers.resource_storage_prefix}

    # IBlueprint

    def get_blueprint(self):
        return blueprint

    # IActions

    def get_actions(self):
        return {'get_resource_download_spec': actions.get_resource_download_spec}

    # IAuthorizationBindings

    def register_authz_bindings(self, authorizer):
        """Authorization Bindings

        This aliases CKANs Resource entity and actions to scopes understood by
        Giftless' JWT authorization scheme
        """
        authorizer.register_type_alias('obj', 'res')
        authorizer.register_action_alias('write', 'update', 'res')
