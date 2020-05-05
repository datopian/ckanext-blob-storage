"""ckanext-external-storage Flask blueprints
"""
from ckan import model
from ckan.lib import uploader
from ckan.plugins import toolkit
from flask import Blueprint, send_file

blueprint = Blueprint(
    'extstorage',
    __name__,
)


def download(resource_id, filename=None, **__):
    """Redirect to an LFS provided download URL or fall back to default
    download method if resource is not managed by External Storage
    """
    context = {
        'model': model,
        'user': toolkit.c.user,
        'auth_user_obj': toolkit.c.userobj,
    }
    try:
        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Unauthorized to read resource {0}'.format(resource_id)))

    if resource.get('url_type') == 'upload' and resource.get('lfs_prefix'):
        # We are in LFS land!
        return redirect_to_external_storage(context, resource, filename)
    return fallback_download_method(resource)


blueprint.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download', view_func=download)
blueprint.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download/<filename>', view_func=download)


def redirect_to_external_storage(context, resource, filename):
    """Get the download URL from LFS server and redirect the user there
    """
    data_dict = {'resource': resource}
    resource_download_spec = toolkit.get_action('get_resource_download_spec')(context, data_dict)
    href = resource_download_spec.get('href')
    if href:
        return toolkit.redirect_to(href)
    else:
        return toolkit.abort(404, _(u'No download is available'))


def fallback_download_method(resource):
    """Fall back to the built in CKAN download method, or a customized
    view function
    """
    if resource.get('url_type') == 'upload':
        upload = uploader.get_resource_uploader(resource)
        filepath = upload.get_path(resource[u'id'])
        return send_file(filepath)
    elif u'url' not in resource:
        return toolkit.abort(404, _(u'No download is available'))

    return toolkit.redirect_to(resource[u'url'])
