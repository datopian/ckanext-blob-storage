import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.authz_service.interfaces import IAuthorizationBindings


class ExternalStoragePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(IAuthorizationBindings)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'external-storage')

    # ITemplateHelpers

    def get_helpers(self):
        return {}

    # IAuthorizationBindings

    def register_authz_bindings(self, authorizer):
        """Authorization Bindings

        This aliases CKANs Resource entity and actions to scopes understood by
        Giftless' JWT authorization scheme
        """
        authorizer.register_type_alias('obj', 'res')
        authorizer.register_action_alias('write', 'update', 'res')
